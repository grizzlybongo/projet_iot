"""
Contrôleur Central de la Serre Intelligente
Rôle : Agréger capteurs, appliquer règles métier, piloter actionneurs
"""
import paho.mqtt.client as mqtt
import json
import logging
import os
from datetime import datetime
from config import BROKER_HOST, BROKER_PORT, BROKER_KEEPALIVE
from config import TOPICS, THRESHOLDS
from config import DAY_START_HOUR, DAY_END_HOUR

# ============================================================
# CONFIGURATION DU LOGGING (UTF-8)
# ============================================================
LOG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs", "greenhouse.log")
os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE, encoding='utf-8'),
        logging.StreamHandler()
    ]
)
class GreenhouseController:
    """Contrôleur central avec règles métier"""

    def __init__(self):
        # Stockage état capteurs
        self.sensor_data = {
            'temp_soil': None,
            'humidity': None,
            'light': None,
            'water_level': None
        }

        # Stockage état actionneurs
        self.actuator_states = {
            'irrigation': 'OFF',
            'lighting': 'OFF'
        }

        # Client MQTT
        self.client = mqtt.Client(
        callback_api_version=mqtt.CallbackAPIVersion.VERSION1,
        client_id='greenhouse_controller'
)
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message

        logging.info('🧠 Contrôleur initialisé')
        # State to avoid repeated temperature alerts
        self.temperature_alert_sent = False
    # ============================================================
    # CALLBACKS MQTT
    # ============================================================
    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            logging.info('✅ Contrôleur connecté au broker')
            client.subscribe('greenhouse/sensors/#', qos=0)
            logging.info('📡 Abonné à tous les capteurs')
            client.subscribe('greenhouse/actuators/+/state', qos=1)
            logging.info('📡 Abonné aux états actionneurs')
        else:
            logging.error(f'❌ Échec connexion (code {rc})')
    
    def on_message(self, client, userdata, msg):
        try:
            data = json.loads(msg.payload.decode())
            if 'sensors' in msg.topic:
                self.handle_sensor_data(msg.topic, data)
            elif 'state' in msg.topic:
                self.handle_actuator_state(msg.topic, data)
        except json.JSONDecodeError:
            logging.error(f'JSON invalide sur {msg.topic}')
        except Exception as e:
            logging.error(f'Erreur traitement: {e}')
    # ============================================================
    # TRAITEMENT DES CAPTEURS
    # ============================================================
    def handle_sensor_data(self, topic, data):
        """Traite les données capteur et applique règles métier"""
        if 'temp_soil' in topic:
            self.sensor_data['temp_soil'] = float(f"{data['value']:.1f}")
            logging.info(f'🌡️ Température sol: {self.sensor_data["temp_soil"]}°C')
        elif 'humidity' in topic:
            self.sensor_data['humidity'] = float(f"{data['value']:.1f}")
            logging.info(f'💧 Humidité: {self.sensor_data["humidity"]}%')
        elif 'light' in topic:
            self.sensor_data['light'] = float(f"{data['value']:.0f}")
            logging.info(f'☀️ Luminosité: {self.sensor_data["light"]} lux')
        elif 'water' in topic:
            self.sensor_data['water_level'] = float(f"{data['value']:.1f}")
            logging.info(f'🚰 Niveau eau: {self.sensor_data["water_level"]}%')

        # Appliquer règles après chaque réception
        self.apply_rules()

    # ============================================================
    # RÈGLES MÉTIER
    # ============================================================
    def apply_rules(self):
        self.check_irrigation()
        self.check_lighting()
        self.check_temperature_alert()
    def check_irrigation(self):
        humidity = self.sensor_data.get('humidity')
        water_level = self.sensor_data.get('water_level')
        if humidity is None or water_level is None:
            return

        should_irrigate = humidity < THRESHOLDS['humidity_low'] and water_level > THRESHOLDS['water_min']
        desired_state = 'ON' if should_irrigate else 'OFF'

        if desired_state != self.actuator_states['irrigation']:
            self.send_command('irrigation', desired_state)
            if desired_state == 'ON':
                logging.warning(f'🚨 Irrigation activée: Humidité={humidity}% < {THRESHOLDS["humidity_low"]}%')
            else:
                logging.info('🛑 Irrigation désactivée')


    def check_lighting(self):
        light = self.sensor_data.get('light')
        if light is None:
            return

        current_hour = datetime.now().hour
        is_daytime = DAY_START_HOUR <= current_hour < DAY_END_HOUR
        should_light = light < THRESHOLDS['light_low'] and is_daytime
        desired_state = 'ON' if should_light else 'OFF'

        if desired_state != self.actuator_states['lighting']:
            self.send_command('lighting', desired_state)
            if desired_state == 'ON':
                logging.warning(f'💡 Éclairage activé: Luminosité={light} lux < {THRESHOLDS["light_low"]} lux')
            else:
                logging.info('🌑 Éclairage désactivé')

    def check_temperature_alert(self):
        """Check for critical soil temperature and publish an alert once.

        Sends an alert message to the ALERTS topic when the soil temperature
        reaches or exceeds the critical threshold, and sends a recovery
        message when it drops back below the threshold. Uses a simple
        latching flag to avoid spamming the alert topic.
        """
        temp = self.sensor_data.get('temp_soil')
        if temp is None:
            return

        critical = THRESHOLDS.get('temp_critical')
        if critical is None:
            return

        # If temperature is critical and we haven't alerted yet -> alert
        if temp >= critical and not self.temperature_alert_sent:
            alert = {
                'type': 'temperature_critical',
                'value': temp,
                'threshold': critical,
                'timestamp': datetime.now().isoformat()
            }
            try:
                self.client.publish(TOPICS['alerts'], json.dumps(alert), qos=1)
                logging.critical(f'🔥 Température critique: {temp}°C >= {critical}°C — alerte envoyée')
            except Exception as e:
                logging.error(f'Erreur envoi alerte température: {e}')
            self.temperature_alert_sent = True

        # If temperature has recovered and we had sent an alert before -> recover
        if temp < critical and self.temperature_alert_sent:
            recover = {
                'type': 'temperature_recovered',
                'value': temp,
                'threshold': critical,
                'timestamp': datetime.now().isoformat()
            }
            try:
                self.client.publish(TOPICS['alerts'], json.dumps(recover), qos=1)
                logging.info(f'✅ Température revenue à la normale: {temp}°C < {critical}°C')
            except Exception as e:
                logging.error(f'Erreur envoi message récupération température: {e}')
            self.temperature_alert_sent = False

    # ============================================================
    # ACTIONNEURS
    # ============================================================
    def handle_actuator_state(self, topic, data):
        if 'irrigation' in topic:
            self.actuator_states['irrigation'] = data['state']
            logging.info(f'💧 État irrigation: {data["state"]}')
        elif 'lighting' in topic:
            self.actuator_states['lighting'] = data['state']
            logging.info(f'💡 État éclairage: {data["state"]}')


    def send_command(self, actuator, action):
        topic_map = {
            'irrigation': TOPICS['actuators']['irrigation']['cmd'],
            'lighting': TOPICS['actuators']['lighting']['cmd']
        }
        topic = topic_map.get(actuator)
        if not topic:
            return

        command = {
            'action': action,
            'timestamp': datetime.now().isoformat(),
            'source': 'controller'
        }
        self.client.publish(topic, json.dumps(command), qos=1)
        logging.info(f'📤 Commande envoyée: {actuator} → {action}'  )    
            

    # ============================================================
    # DÉMARRAGE
    # ============================================================
    def start(self):
        try:
            self.client.connect(BROKER_HOST, BROKER_PORT, BROKER_KEEPALIVE)
            logging.info('🚀 Contrôleur démarré')
            self.client.loop_forever()
        except KeyboardInterrupt:
            logging.info('🛑 Arrêt contrôleur')
        finally:
            self.client.disconnect()

    # ============================================================
    # POINT D’ENTRÉE
    # ============================================================
if __name__ == '__main__':
    controller = GreenhouseController()
    controller.start()
