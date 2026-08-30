import asyncio
from datetime import datetime, timezone
from app.my_database import relief_camp_collection

CAMPS_DATA = [
  {
    "dsArea": "Kaduwela",
    "gnDivision": "Boralugoda",
    "name": "Sri Maha Viharaya Pore",
    "maxCapacityPersons": 50,
    "maxFamilies": 15,
    "latitude": 6.872,
    "longitude": 80.01,
    "coordinateType": "Approx"
  },
  {
    "dsArea": "Kaduwela",
    "gnDivision": "Hewagama",
    "name": "Abhinawarama Viharasthanaya",
    "maxCapacityPersons": 1350,
    "maxFamilies": 300,
    "latitude": 6.948,
    "longitude": 79.955,
    "coordinateType": "Approx"
  },
  {
    "dsArea": "Kaduwela",
    "gnDivision": "Hewagama",
    "name": "Hewagama Kanishta Viddyalaya",
    "maxCapacityPersons": 500,
    "maxFamilies": 100,
    "latitude": 6.949,
    "longitude": 79.956,
    "coordinateType": "Approx"
  },
  {
    "dsArea": "Kaduwela",
    "gnDivision": "Ihala Bomiriya",
    "name": "Ihala Bomiriya Kanishta Viddyalaya",
    "maxCapacityPersons": 750,
    "maxFamilies": 150,
    "latitude": 6.933,
    "longitude": 80.006,
    "coordinateType": "Approx"
  },
  {
    "dsArea": "Kaduwela",
    "gnDivision": "Korathota",
    "name": "Welihin Thuduwa Praja Shalawa",
    "maxCapacityPersons": 100,
    "maxFamilies": 30,
    "latitude": 6.908,
    "longitude": 80.0013,
    "coordinateType": "Confirmed"
  },
  {
    "dsArea": "Kaduwela",
    "gnDivision": "Korathota",
    "name": "Sampath Pura Viharasthanaya",
    "maxCapacityPersons": 100,
    "maxFamilies": 30,
    "latitude": 6.908,
    "longitude": 80.0013,
    "coordinateType": "Confirmed"
  },
  {
    "dsArea": "Kaduwela",
    "gnDivision": "Korathota",
    "name": "Rajasinghe Mawatha, Praja Shalawa",
    "maxCapacityPersons": 50,
    "maxFamilies": 10,
    "latitude": 6.908,
    "longitude": 80.0013,
    "coordinateType": "Confirmed"
  },
  {
    "dsArea": "Kaduwela",
    "gnDivision": "Kothalawala",
    "name": "SiriSamadhi Bouddha Maddyastanaya",
    "maxCapacityPersons": 75,
    "maxFamilies": 25,
    "latitude": 6.905,
    "longitude": 79.975,
    "coordinateType": "Approx"
  },
  {
    "dsArea": "Kaduwela",
    "gnDivision": "Nawagamuwa",
    "name": "Pilip Thilakawardana Viddyalaya",
    "maxCapacityPersons": 400,
    "maxFamilies": 100,
    "latitude": 6.9241,
    "longitude": 80.018,
    "coordinateType": "Confirmed"
  },
  {
    "dsArea": "Kaduwela",
    "gnDivision": "Nawagamuwa South",
    "name": "Sanasa Samithi Shalawa",
    "maxCapacityPersons": 85,
    "maxFamilies": 20,
    "latitude": 6.918,
    "longitude": 80.017,
    "coordinateType": "Approx"
  },
  {
    "dsArea": "Kaduwela",
    "gnDivision": "Nawagamuwa South",
    "name": "Maithry Bodhi Viharaya",
    "maxCapacityPersons": 60,
    "maxFamilies": 15,
    "latitude": 6.918,
    "longitude": 80.017,
    "coordinateType": "Approx"
  },
  {
    "dsArea": "Kaduwela",
    "gnDivision": "Oruwala",
    "name": "Oruwala Sri BodhirukKharama Viharaya",
    "maxCapacityPersons": 100,
    "maxFamilies": 20,
    "latitude": 6.933,
    "longitude": 79.984,
    "coordinateType": "Approx"
  },
  {
    "dsArea": "Kaduwela",
    "gnDivision": "Oruwala",
    "name": "Oruwala Kanishta Viddyalaya",
    "maxCapacityPersons": 400,
    "maxFamilies": 80,
    "latitude": 6.933,
    "longitude": 79.984,
    "coordinateType": "Approx"
  },
  {
    "dsArea": "Kaduwela",
    "gnDivision": "Pahala Bomiriya",
    "name": "Munidasa Kumarathunga Viddyalaya",
    "maxCapacityPersons": 200,
    "maxFamilies": 50,
    "latitude": 6.92,
    "longitude": 80.0,
    "coordinateType": "Approx"
  },
  {
    "dsArea": "Kaduwela",
    "gnDivision": "Pahala Bomiriya",
    "name": "Gunasekararamaya",
    "maxCapacityPersons": 80,
    "maxFamilies": 20,
    "latitude": 6.92,
    "longitude": 80.0,
    "coordinateType": "Approx"
  },
  {
    "dsArea": "Kaduwela",
    "gnDivision": "Pahala Bomiriya",
    "name": "Ihala Bomiriya Sanasa",
    "maxCapacityPersons": 60,
    "maxFamilies": 15,
    "latitude": 6.92,
    "longitude": 80.0,
    "coordinateType": "Approx"
  },
  {
    "dsArea": "Kaduwela",
    "gnDivision": "Pahala Bomiriya",
    "name": "Karalgahahena Sanasa",
    "maxCapacityPersons": 20,
    "maxFamilies": 5,
    "latitude": 6.92,
    "longitude": 80.0,
    "coordinateType": "Approx"
  },
  {
    "dsArea": "Kaduwela",
    "gnDivision": "Pahala Bomiriya B",
    "name": "Yakala Sri Silalankara Viddyalaya",
    "maxCapacityPersons": 579,
    "maxFamilies": 125,
    "latitude": 6.9232,
    "longitude": 80.0027,
    "coordinateType": "Confirmed"
  },
  {
    "dsArea": "Kaduwela",
    "gnDivision": "Pahala Bomiriya B",
    "name": "Sri Shaylabimbarama Viharaya",
    "maxCapacityPersons": 150,
    "maxFamilies": 46,
    "latitude": 6.9232,
    "longitude": 80.0027,
    "coordinateType": "Confirmed"
  },
  {
    "dsArea": "Kaduwela",
    "gnDivision": "Pahala Bomiriya B",
    "name": "Sanasa Samithi Shalawa",
    "maxCapacityPersons": 75,
    "maxFamilies": 20,
    "latitude": 6.9232,
    "longitude": 80.0027,
    "coordinateType": "Confirmed"
  },
  {
    "dsArea": "Kaduwela",
    "gnDivision": "Pahala Bomiriya B",
    "name": "Morawaka Watta Praja Shalawa",
    "maxCapacityPersons": 35,
    "maxFamilies": 12,
    "latitude": 6.9232,
    "longitude": 80.0027,
    "coordinateType": "Confirmed"
  },
  {
    "dsArea": "Kaduwela",
    "gnDivision": "Shanthalokagama",
    "name": "Sri Dharmashrama Maddyastanaya",
    "maxCapacityPersons": 40,
    "maxFamilies": 10,
    "latitude": 6.93,
    "longitude": 79.98,
    "coordinateType": "Approx"
  },
  {
    "dsArea": "Kaduwela",
    "gnDivision": "Thunadahena",
    "name": "Pelangahawatta praja shalawa",
    "maxCapacityPersons": 15,
    "maxFamilies": 3,
    "latitude": 6.928,
    "longitude": 79.975,
    "coordinateType": "Approx"
  },
  {
    "dsArea": "Kaduwela",
    "gnDivision": "Thunadahena",
    "name": "imosque",
    "maxCapacityPersons": 35,
    "maxFamilies": 8,
    "latitude": 6.928,
    "longitude": 79.975,
    "coordinateType": "Approx"
  },
  {
    "dsArea": "Kaduwela",
    "gnDivision": "Udumulla",
    "name": "Sri Purwarama Viharasthanaya Udumulla",
    "maxCapacityPersons": 100,
    "maxFamilies": 20,
    "latitude": 6.9096,
    "longitude": 79.9612,
    "coordinateType": "Approx"
  },
  {
    "dsArea": "Kaduwela",
    "gnDivision": "Wekewatta",
    "name": "Ashokarama Viharasthanaya",
    "maxCapacityPersons": 50,
    "maxFamilies": 10,
    "latitude": 6.925,
    "longitude": 79.998,
    "coordinateType": "Approx"
  },
  {
    "dsArea": "Kaduwela",
    "gnDivision": "Wekewatta",
    "name": "Seva Piyasa",
    "maxCapacityPersons": 20,
    "maxFamilies": 4,
    "latitude": 6.925,
    "longitude": 79.998,
    "coordinateType": "Approx"
  },
  {
    "dsArea": "Kaduwela",
    "gnDivision": "Welihinda",
    "name": "Praja Shalawa",
    "maxCapacityPersons": 180,
    "maxFamilies": 36,
    "latitude": 6.928,
    "longitude": 79.995,
    "coordinateType": "Approx"
  },
  {
    "dsArea": "Kaduwela",
    "gnDivision": "Welivita",
    "name": "Welivita Shantha Mariya Viddyalaya",
    "maxCapacityPersons": 800,
    "maxFamilies": 200,
    "latitude": 6.9331,
    "longitude": 79.9687,
    "coordinateType": "Approx"
  }
]

async def run_import():
    docs = []
    for item in CAMPS_DATA:
        doc = {
            "dsArea": item["dsArea"],
            "gnDivision": item["gnDivision"],
            "name": item["name"],
            "maxCapacityPersons": int(item["maxCapacityPersons"]),
            "maxFamilies": int(item["maxFamilies"]),
            "currentPopulation": 0,
            "predictedPopulation": 0,
            "assignedVolunteerIds": [],
            "latitude": item.get("latitude"),
            "longitude": item.get("longitude"),
            "coordinateType": item.get("coordinateType"),
            "hourlyHistory": [],
            "lastUpdated": datetime.now(timezone.utc)
        }
        docs.append(doc)
    
    result = await relief_camp_collection.insert_many(docs)
    print(f"Successfully inserted {len(result.inserted_ids)} relief camps into database.")

if __name__ == "__main__":
    asyncio.run(run_import())
