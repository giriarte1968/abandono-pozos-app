from frontend.services.mock_api_client import MockApiClient
import json

client = MockApiClient()
print("--- LOGISTICS MOCK DATA ---")
logistics = client.get_all_logistics()
print(f"Total entries: {len(logistics)}")
if logistics:
    print(json.dumps(logistics[0], indent=2))

print("\n--- SUPPLIES MOCK DATA ---")
supplies = client.get_all_supplies_status()
print(f"Total entries: {len(supplies)}")
print("\n--- SPECIFIC PROJECT (BLOQUEADO: Z-789) ---")
detail = client.get_project_detail("Z-789")
if detail:
    print(f"Status: {detail['status']}")
    print("Transport status:", [f"{t['type']}: {t['status']}" for t in detail['transport_list']])
    print("Equipos status:", [f"{e['name']}: {e['status']}" for e in detail['equipment_list']])
