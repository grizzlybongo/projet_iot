# Serre Intelligente

Simulation d'une serre connectée : quatre capteurs (température du sol, humidité, luminosité, niveau d'eau), deux actionneurs (irrigation, éclairage) et un contrôleur central. Tous les composants communiquent entre eux uniquement par MQTT, via un broker local. Le contrôleur reçoit les mesures, applique les règles métier et publie les commandes.

## Architecture

```text
 Capteurs ───► Broker MQTT ───► Contrôleur ───► Broker MQTT ───► Actionneurs
 (4 capteurs)                  (règles métier)                   (irrigation, éclairage)
      ▲                             ▲                                  │
      └─────────────────────────────┴──── états (…/state) ◄─────────────┘
```

Topics MQTT (définis dans `config.py`) :

| Rôle | Topic |
|---|---|
| Température du sol | `greenhouse/sensors/temp_soil` |
| Humidité | `greenhouse/sensors/humidity` |
| Luminosité | `greenhouse/sensors/light` |
| Niveau d'eau | `greenhouse/sensors/water_level` |
| Commande irrigation | `greenhouse/actuators/irrigation/cmd` |
| État irrigation | `greenhouse/actuators/irrigation/state` |
| Commande éclairage | `greenhouse/actuators/lighting/cmd` |
| État éclairage | `greenhouse/actuators/lighting/state` |
| Alertes | `greenhouse/alerts` |

## Règles métier

- **Irrigation** : humidité < **40 %** ET niveau d'eau > **20 %** → `ON`, sinon `OFF`.
- **Éclairage** : luminosité < **300 lux** ET heure comprise entre **8 h et 18 h** (`DAY_START_HOUR` / `DAY_END_HOUR`) → `ON`, sinon `OFF`.

Les seuils sont lus dans `THRESHOLDS` (`humidity_low`, `water_min`, `light_low`).

## Prérequis

- Python 3.10 ou plus récent
- Un broker Mosquitto local sur `localhost:1883`
- `pip install -r requirements.txt`

## Lancement

Un terminal par composant, **toujours depuis la racine du projet** :

```bash
python controller.py
python -m actuators.irrigation
python -m actuators.lighting
python -m sensors.temp_soil
python -m sensors.humidity
python -m sensors.light
python -m sensors.water
```

Astuce : `mosquitto_sub -t 'greenhouse/#' -v` pour observer le trafic MQTT.

## Configuration

Tout est centralisé dans `config.py` : hôte/port du broker, topics, seuils métier, intervalles de publication, plages de simulation des capteurs et pas de la marche aléatoire (`SENSOR_STEPS`). Modifier ce fichier suffit pour changer le comportement de la simulation.

## Structure du projet

```text
greenhouse/
├── config.py
├── controller.py
├── requirements.txt
├── README.md
├── sensors/
│   ├── base_sensor.py
│   ├── temp_soil.py
│   ├── humidity.py
│   ├── light.py
│   └── water.py
├── actuators/
│   ├── base_actuator.py
│   ├── irrigation.py
│   └── lighting.py
└── logs/
    ├── .gitkeep
    └── greenhouse.log
```

## Limites connues

- Le contrôleur envoie des commandes JSON, alors que `irrigation.py` / `lighting.py` attendent `ON` / `OFF` et publient un état en texte brut.
- `irrigation.py` et `lighting.py` sont procéduraux et n'utilisent pas `BaseActuator`.
- `controller.py` appelle `self.check_temperature_alert()` (méthode signalée comme absente dans la version de référence, laissée inchangée ici).
