"""
Contrôleur Central de la Serre Intelligente
Rôle : Agréger capteurs, appliquer règles métier, piloter actionneurs
"""
import paho.mqtt.client as mqtt
import json
import logging
from datetime import datetime
from config import BROKER_HOST, BROKER_PORT, BROKER_KEEPALIVE
from config import TOPICS, THRESHOLDS

# ============================================================
# CONFIGURATION DU LOGGING (UTF-8)
# ============================================================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler('logs/greenhouse.log', encoding='utf-8'),
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
            logging.info(f' Humidité: {self.sensor_data["humidity"]}%')
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
            is_daytime = 8 <= current_hour < 18
            should_light = light < THRESHOLDS['light_low'] and is_daytime
            desired_state = 'ON' if should_light else 'OFF'

            if desired_state != self.actuator_states['lighting']:
                self.send_command('lighting', desired_state)
                if desired_state == 'ON':
                    logging.warning(f'💡 Éclairage activé: Luminosité={light} lux < {THRESHOLDS["light_low"]} lux')
                else:
                    logging.info('🌑 Éclairage désactivé')

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
