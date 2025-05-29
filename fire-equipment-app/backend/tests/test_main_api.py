import json
from tests.test_config import BaseTestCase
from app.models import User, Equipment, db # Adjust import

class MainApiTestCase(BaseTestCase):
    def _get_auth_token(self, username='apiuser', password='apipass'):
        # Helper to register and login a user to get a token
        self.client.post('/auth/register', 
                         data=json.dumps({'username': username, 'password': password}), 
                         content_type='application/json')
        response = self.client.post('/auth/login', 
                                    data=json.dumps({'username': username, 'password': password}), 
                                    content_type='application/json')
        return json.loads(response.get_data(as_text=True))['token']

    def test_create_equipment_no_token(self):
        response = self.client.post('/api/equipment',
                                   data=json.dumps({'name': 'Test Hose', 'category': 'Hoses'}),
                                   content_type='application/json')
        self.assertEqual(response.status_code, 401) 
        self.assertIn('Token is missing', response.get_data(as_text=True))

    def test_create_equipment_with_token(self):
        token = self._get_auth_token()
        response = self.client.post('/api/equipment',
                                   headers={'x-access-token': token},
                                   data=json.dumps({'name': 'Test SCBA Pack Alpha', 'category': 'SCBA', 'description': 'A test SCBA pack'}),
                                   content_type='application/json')
        self.assertEqual(response.status_code, 201)
        data = json.loads(response.get_data(as_text=True))
        self.assertIn('Equipment created', data['message'])
        self.assertTrue('id' in data)
        
        # Verify it's in the database
        equipment_id = data['id']
        equipment = Equipment.query.get(equipment_id)
        self.assertIsNotNone(equipment)
        self.assertEqual(equipment.name, 'Test SCBA Pack Alpha')

    def test_get_all_equipment_with_token(self):
        token = self._get_auth_token()
        # Create some equipment first
        self.client.post('/api/equipment',
                         headers={'x-access-token': token},
                         data=json.dumps({'name': 'Hose A', 'category': 'Hoses'}),
                         content_type='application/json')
        self.client.post('/api/equipment',
                         headers={'x-access-token': token},
                         data=json.dumps({'name': 'Ladder B', 'category': 'Ladders'}),
                         content_type='application/json')

        response = self.client.get('/api/equipment', headers={'x-access-token': token})
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.get_data(as_text=True))
        self.assertTrue('equipment' in data)
        self.assertEqual(len(data['equipment']), 2)
        self.assertEqual(data['equipment'][0]['name'], 'Hose A')
        self.assertEqual(data['equipment'][1]['name'], 'Ladder B')

    def test_get_specific_equipment_with_token(self):
        token = self._get_auth_token()
        create_response = self.client.post('/api/equipment',
                                           headers={'x-access-token': token},
                                           data=json.dumps({'name': 'Specific Nozzle', 'category': 'Nozzles'}),
                                           content_type='application/json')
        equipment_id = json.loads(create_response.get_data(as_text=True))['id']

        response = self.client.get(f'/api/equipment/{equipment_id}', headers={'x-access-token': token})
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.get_data(as_text=True))
        self.assertEqual(data['name'], 'Specific Nozzle')
        self.assertEqual(data['id'], equipment_id)

    def test_update_equipment_with_token(self):
        token = self._get_auth_token()
        create_response = self.client.post('/api/equipment',
                                           headers={'x-access-token': token},
                                           data=json.dumps({'name': 'Old Name', 'category': 'Tools'}),
                                           content_type='application/json')
        equipment_id = json.loads(create_response.get_data(as_text=True))['id']

        response = self.client.put(f'/api/equipment/{equipment_id}',
                                   headers={'x-access-token': token},
                                   data=json.dumps({'name': 'New Name', 'description': 'Updated Description'}),
                                   content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertIn('Equipment updated', response.get_data(as_text=True))

        updated_equipment = Equipment.query.get(equipment_id)
        self.assertEqual(updated_equipment.name, 'New Name')
        self.assertEqual(updated_equipment.description, 'Updated Description')

    def test_delete_equipment_with_token(self):
        token = self._get_auth_token()
        create_response = self.client.post('/api/equipment',
                                           headers={'x-access-token': token},
                                           data=json.dumps({'name': 'To Be Deleted', 'category': 'Misc'}),
                                           content_type='application/json')
        equipment_id = json.loads(create_response.get_data(as_text=True))['id']

        response = self.client.delete(f'/api/equipment/{equipment_id}', headers={'x-access-token': token})
        self.assertEqual(response.status_code, 200)
        self.assertIn('Equipment deleted', response.get_data(as_text=True))

        deleted_equipment = Equipment.query.get(equipment_id)
        self.assertIsNone(deleted_equipment)

    # Basic tests for Checklist Templates
    def test_create_checklist_template(self):
        token = self._get_auth_token()
        # First, create an equipment item to link
        eq_response = self.client.post('/api/equipment',
                                       headers={'x-access-token': token},
                                       data=json.dumps({'name': 'Test Ladder for Template', 'category': 'Ladders'}),
                                       content_type='application/json')
        self.assertEqual(eq_response.status_code, 201)
        equipment_id = json.loads(eq_response.get_data(as_text=True))['id']

        template_data = {
            "name": "Daily Truck Check",
            "type": "daily",
            "description": "Daily check for Engine 1",
            "items": [
                {"item_description": "Check oil level", "expected_status": "Full"},
                {"item_description": "Check tire pressure", "equipment_id": equipment_id}
            ]
        }
        response = self.client.post('/api/checklist-templates',
                                    headers={'x-access-token': token},
                                    data=json.dumps(template_data),
                                    content_type='application/json')
        self.assertEqual(response.status_code, 201)
        data = json.loads(response.get_data(as_text=True))
        self.assertIn('Checklist template created', data['message'])
        self.assertTrue('id' in data)
        
        # Verify in DB
        template = ChecklistTemplate.query.get(data['id'])
        self.assertIsNotNone(template)
        self.assertEqual(template.name, "Daily Truck Check")
        self.assertEqual(len(template.items), 2)
        self.assertEqual(template.items[1].equipment_id, equipment_id)

    def test_get_all_checklist_templates(self):
        token = self._get_auth_token()
        # Create a template first
        eq_response = self.client.post('/api/equipment',
                                       headers={'x-access-token': token},
                                       data=json.dumps({'name': 'Test Hose for Template', 'category': 'Hoses'}),
                                       content_type='application/json')
        equipment_id = json.loads(eq_response.get_data(as_text=True))['id']
        template_data = {
            "name": "Weekly Hose Check",
            "type": "weekly",
            "items": [{"item_description": "Inspect nozzle", "equipment_id": equipment_id}]
        }
        self.client.post('/api/checklist-templates', headers={'x-access-token': token}, data=json.dumps(template_data), content_type='application/json')

        response = self.client.get('/api/checklist-templates', headers={'x-access-token': token})
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.get_data(as_text=True))
        self.assertTrue('checklist_templates' in data)
        self.assertGreaterEqual(len(data['checklist_templates']), 1)
        self.assertEqual(data['checklist_templates'][0]['name'], "Weekly Hose Check")

    # Basic tests for Checklist Submissions
    def test_submit_checklist(self):
        token = self._get_auth_token()
        # Create equipment and template
        eq_response = self.client.post('/api/equipment',
                                       headers={'x-access-token': token},
                                       data=json.dumps({'name': 'Test Air Tank', 'category': 'SCBA'}),
                                       content_type='application/json')
        equipment_id = json.loads(eq_response.get_data(as_text=True))['id']
        
        template_data = {
            "name": "SCBA Check", "type": "daily",
            "items": [{"item_description": "Check air pressure", "equipment_id": equipment_id, "expected_status": "Full"}]
        }
        template_response = self.client.post('/api/checklist-templates', headers={'x-access-token': token}, data=json.dumps(template_data), content_type='application/json')
        template_id = json.loads(template_response.get_data(as_text=True))['id']

        checklist_data = {
            "checklist_template_id": template_id,
            "items": [
                {
                    "item_description_from_template": "Check air pressure",
                    "status": "full", # Ensure this matches expected values or model constraints
                    "equipment_id": equipment_id,
                    "notes": "All good"
                }
            ]
        }
        response = self.client.post('/api/checklists',
                                    headers={'x-access-token': token},
                                    data=json.dumps(checklist_data),
                                    content_type='application/json')
        self.assertEqual(response.status_code, 201, response.get_data(as_text=True))
        data = json.loads(response.get_data(as_text=True))
        self.assertIn('Checklist submitted successfully', data['message'])
        self.assertTrue('id' in data)

        # Verify in DB
        checklist = Checklist.query.get(data['id'])
        self.assertIsNotNone(checklist)
        self.assertEqual(checklist.checklist_template_id, template_id)
        self.assertEqual(len(checklist.items), 1)
        self.assertEqual(checklist.items[0].status, "full")

    def test_get_user_checklists(self):
        token = self._get_auth_token(username="checklistuser", password="password")
        # Submit a checklist first (similar setup to test_submit_checklist)
        eq_response = self.client.post('/api/equipment', headers={'x-access-token': token}, data=json.dumps({'name': 'Test Axe', 'category': 'Tools'}), content_type='application/json')
        equipment_id = json.loads(eq_response.get_data(as_text=True))['id']
        template_data = {"name": "Tool Check", "type": "shift", "items": [{"item_description": "Inspect Axe Handle", "equipment_id": equipment_id}]}
        template_response = self.client.post('/api/checklist-templates', headers={'x-access-token': token}, data=json.dumps(template_data), content_type='application/json')
        template_id = json.loads(template_response.get_data(as_text=True))['id']
        checklist_data = {"checklist_template_id": template_id, "items": [{"item_description_from_template": "Inspect Axe Handle", "status": "good", "equipment_id": equipment_id}]}
        self.client.post('/api/checklists', headers={'x-access-token': token}, data=json.dumps(checklist_data), content_type='application/json')

        response = self.client.get('/api/checklists', headers={'x-access-token': token})
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.get_data(as_text=True))
        self.assertTrue('checklists' in data)
        self.assertGreaterEqual(len(data['checklists']), 1)
        self.assertEqual(data['checklists'][0]['template_name'], "Tool Check")
        self.assertEqual(len(data['checklists'][0]['items']), 1)
        self.assertEqual(data['checklists'][0]['items'][0]['status'], "good")

    def test_get_equipment_history(self):
        token = self._get_auth_token(username="historyuser", password="password")
        # Create equipment
        eq_response = self.client.post('/api/equipment',
                                       headers={'x-access-token': token},
                                       data=json.dumps({'name': 'Test Monitor', 'category': 'Electronics'}),
                                       content_type='application/json')
        equipment_id = json.loads(eq_response.get_data(as_text=True))['id']
        
        # Create a template that uses this equipment
        template_data = {
            "name": "Monitor Check", "type": "daily",
            "items": [{"item_description": "Check power", "equipment_id": equipment_id, "expected_status": "on"}]
        }
        template_response = self.client.post('/api/checklist-templates', headers={'x-access-token': token}, data=json.dumps(template_data), content_type='application/json')
        template_id = json.loads(template_response.get_data(as_text=True))['id']

        # Submit a checklist for this equipment
        checklist_data = {
            "checklist_template_id": template_id,
            "items": [
                {
                    "item_description_from_template": "Check power",
                    "status": "on",
                    "equipment_id": equipment_id,
                    "notes": "Monitor is working"
                }
            ]
        }
        self.client.post('/api/checklists', headers={'x-access-token': token}, data=json.dumps(checklist_data), content_type='application/json')

        # Get equipment history
        response = self.client.get(f'/api/equipment/{equipment_id}/history', headers={'x-access-token': token})
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.get_data(as_text=True))
        self.assertTrue('history' in data)
        self.assertEqual(len(data['history']), 1)
        self.assertEqual(data['history'][0]['equipment_id'], equipment_id)
        self.assertEqual(data['history'][0]['status'], "on")
        self.assertEqual(data['history'][0]['description_from_check'], "Check power")

    def test_create_checklist_template_item_without_equipment_id(self):
        token = self._get_auth_token()
        template_data = {
            "name": "General Station Check",
            "type": "daily",
            "description": "General checks around the station",
            "items": [
                {"item_description": "Check coffee machine", "expected_status": "Full"},
                {"item_description": "Tidy common area"} 
            ]
        }
        response = self.client.post('/api/checklist-templates',
                                    headers={'x-access-token': token},
                                    data=json.dumps(template_data),
                                    content_type='application/json')
        self.assertEqual(response.status_code, 201, response.get_data(as_text=True))
        data = json.loads(response.get_data(as_text=True))
        self.assertIn('Checklist template created', data['message'])
        
        # Verify in DB
        template = ChecklistTemplate.query.get(data['id'])
        self.assertIsNotNone(template)
        self.assertEqual(len(template.items), 2)
        self.assertIsNone(template.items[1].equipment_id) # Check that equipment_id can be null

    def test_submit_checklist_item_without_equipment_id(self):
        token = self._get_auth_token(username="checklistuser2", password="password")
        
        template_data = {
            "name": "Morning Prep", "type": "daily",
            "items": [{"item_description": "Ensure briefing room is ready"}]
        }
        template_response = self.client.post('/api/checklist-templates', headers={'x-access-token': token}, data=json.dumps(template_data), content_type='application/json')
        template_id = json.loads(template_response.get_data(as_text=True))['id']

        checklist_data = {
            "checklist_template_id": template_id,
            "items": [
                {
                    "item_description_from_template": "Ensure briefing room is ready",
                    "status": "ready",
                    # No equipment_id here
                    "notes": "All set for morning briefing."
                }
            ]
        }
        response = self.client.post('/api/checklists',
                                    headers={'x-access-token': token},
                                    data=json.dumps(checklist_data),
                                    content_type='application/json')
        self.assertEqual(response.status_code, 201, response.get_data(as_text=True))
        data = json.loads(response.get_data(as_text=True))
        self.assertIn('Checklist submitted successfully', data['message'])

        # Verify in DB
        checklist = Checklist.query.get(data['id'])
        self.assertIsNotNone(checklist)
        self.assertEqual(len(checklist.items), 1)
        self.assertIsNone(checklist.items[0].equipment_id)
        self.assertEqual(checklist.items[0].status, "ready")

    def test_create_checklist_template_item_with_nonexistent_equipment_id(self):
        token = self._get_auth_token()
        template_data = {
            "name": "Invalid Equipment Check",
            "type": "daily",
            "items": [{"item_description": "Check non-existent equipment", "equipment_id": 9999}] # Assuming 9999 doesn't exist
        }
        response = self.client.post('/api/checklist-templates',
                                    headers={'x-access-token': token},
                                    data=json.dumps(template_data),
                                    content_type='application/json')
        self.assertEqual(response.status_code, 400, response.get_data(as_text=True))
        self.assertIn("Equipment with ID 9999 not found", response.get_data(as_text=True))

    def test_submit_checklist_item_with_nonexistent_equipment_id(self):
        token = self._get_auth_token(username="checklistuser3", password="password")
        template_data = {
            "name": "Valid Template for Invalid Check", "type": "daily",
            "items": [{"item_description": "Generic item"}]
        }
        template_response = self.client.post('/api/checklist-templates', headers={'x-access-token': token}, data=json.dumps(template_data), content_type='application/json')
        template_id = json.loads(template_response.get_data(as_text=True))['id']

        checklist_data = {
            "checklist_template_id": template_id,
            "items": [
                {
                    "item_description_from_template": "Generic item",
                    "status": "checked",
                    "equipment_id": 9999 # Assuming 9999 doesn't exist
                }
            ]
        }
        response = self.client.post('/api/checklists',
                                    headers={'x-access-token': token},
                                    data=json.dumps(checklist_data),
                                    content_type='application/json')
        self.assertEqual(response.status_code, 400, response.get_data(as_text=True))
        self.assertIn("Equipment with ID 9999 not found for an item", response.get_data(as_text=True))

    def test_get_specific_checklist_template_with_items(self):
        token = self._get_auth_token()
        # Create equipment
        eq_response = self.client.post('/api/equipment',
                                       headers={'x-access-token': token},
                                       data=json.dumps({'name': 'Ladder Truck 1', 'category': 'Apparatus'}),
                                       content_type='application/json')
        equipment_id = json.loads(eq_response.get_data(as_text=True))['id']

        template_data = {
            "name": "Ladder Truck Daily",
            "type": "daily",
            "description": "Daily inspection for Ladder Truck 1",
            "items": [
                {"item_description": "Check aerial ladder hydraulics", "equipment_id": equipment_id, "expected_status": "Operational"},
                {"item_description": "Verify fuel level", "expected_status": "Full"}
            ]
        }
        create_template_response = self.client.post('/api/checklist-templates',
                                                    headers={'x-access-token': token},
                                                    data=json.dumps(template_data),
                                                    content_type='application/json')
        template_id = json.loads(create_template_response.get_data(as_text=True))['id']

        response = self.client.get(f'/api/checklist-templates/{template_id}', headers={'x-access-token': token})
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.get_data(as_text=True))
        
        self.assertEqual(data['id'], template_id)
        self.assertEqual(data['name'], "Ladder Truck Daily")
        self.assertEqual(len(data['items']), 2)
        self.assertEqual(data['items'][0]['item_description'], "Check aerial ladder hydraulics")
        self.assertEqual(data['items'][0]['equipment_id'], equipment_id)
        self.assertEqual(data['items'][1]['item_description'], "Verify fuel level")
        self.assertIsNone(data['items'][1]['equipment_id']) # This should be None based on the data provided
        
    def test_get_specific_checklist_with_items_and_user_details(self):
        # Register a specific user for this test
        user_data = {'username': 'detailuser', 'password': 'password123'}
        self.client.post('/auth/register', data=json.dumps(user_data), content_type='application/json')
        login_resp = self.client.post('/auth/login', data=json.dumps(user_data), content_type='application/json')
        token = json.loads(login_resp.get_data(as_text=True))['token']
        user_id = json.loads(login_resp.get_data(as_text=True))['user_id']

        # Create equipment
        eq_response = self.client.post('/api/equipment',
                                       headers={'x-access-token': token},
                                       data=json.dumps({'name': 'Rescue Saw', 'category': 'Tools'}),
                                       content_type='application/json')
        equipment_id = json.loads(eq_response.get_data(as_text=True))['id']
        
        # Create a template
        template_data = {
            "name": "Rescue Saw Check", "type": "daily",
            "items": [{"item_description": "Check fuel and chain", "equipment_id": equipment_id}]
        }
        template_response = self.client.post('/api/checklist-templates', headers={'x-access-token': token}, data=json.dumps(template_data), content_type='application/json')
        template_id = json.loads(template_response.get_data(as_text=True))['id']

        # Submit a checklist
        checklist_data = {
            "checklist_template_id": template_id,
            "items": [
                {
                    "item_description_from_template": "Check fuel and chain",
                    "status": "ready",
                    "equipment_id": equipment_id,
                    "notes": "Fuel full, chain sharp."
                }
            ]
        }
        submit_response = self.client.post('/api/checklists', headers={'x-access-token': token}, data=json.dumps(checklist_data), content_type='application/json')
        checklist_id = json.loads(submit_response.get_data(as_text=True))['id']

        # Get the checklist details
        response = self.client.get(f'/api/checklists/{checklist_id}', headers={'x-access-token': token})
        self.assertEqual(response.status_code, 200, response.get_data(as_text=True))
        data = json.loads(response.get_data(as_text=True))

        self.assertEqual(data['id'], checklist_id)
        self.assertEqual(data['user_id'], user_id)
        self.assertEqual(data['checklist_template_id'], template_id)
        self.assertEqual(data['template_name'], "Rescue Saw Check")
        self.assertEqual(len(data['items']), 1)
        self.assertEqual(data['items'][0]['item_description_from_template'], "Check fuel and chain")
        self.assertEqual(data['items'][0]['status'], "ready")
        self.assertEqual(data['items'][0]['equipment_id'], equipment_id)
        self.assertEqual(data['items'][0]['equipment_name'], "Rescue Saw") # Check if equipment name is resolved
        self.assertEqual(data['items'][0]['notes'], "Fuel full, chain sharp.")

    def test_get_equipment_history_multiple_entries(self):
        token = self._get_auth_token(username="historyuser2", password="password")
        # Create equipment
        eq_response = self.client.post('/api/equipment',
                                       headers={'x-access-token': token},
                                       data=json.dumps({'name': 'Generator', 'category': 'Power Tools'}),
                                       content_type='application/json')
        equipment_id = json.loads(eq_response.get_data(as_text=True))['id']
        
        # Create a template
        template_data = {
            "name": "Generator Check", "type": "weekly",
            "items": [{"item_description": "Run test", "equipment_id": equipment_id}]
        }
        template_response = self.client.post('/api/checklist-templates', headers={'x-access-token': token}, data=json.dumps(template_data), content_type='application/json')
        template_id = json.loads(template_response.get_data(as_text=True))['id']

        # Submit a checklist - Entry 1
        checklist_data_1 = {
            "checklist_template_id": template_id,
            "items": [{"item_description_from_template": "Run test", "status": "operational", "equipment_id": equipment_id, "notes": "Ran smoothly"}]
        }
        self.client.post('/api/checklists', headers={'x-access-token': token}, data=json.dumps(checklist_data_1), content_type='application/json')
        
        # Submit another checklist for the same equipment - Entry 2
        checklist_data_2 = {
            "checklist_template_id": template_id,
            "items": [{"item_description_from_template": "Run test", "status": "needs_fuel", "equipment_id": equipment_id, "notes": "Low on fuel"}]
        }
        self.client.post('/api/checklists', headers={'x-access-token': token}, data=json.dumps(checklist_data_2), content_type='application/json')

        # Get equipment history
        response = self.client.get(f'/api/equipment/{equipment_id}/history', headers={'x-access-token': token})
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.get_data(as_text=True))
        self.assertTrue('history' in data)
        self.assertEqual(len(data['history']), 2)
        # Entries should be in descending order of timestamp (most recent first)
        self.assertEqual(data['history'][0]['status'], "needs_fuel")
        self.assertEqual(data['history'][1]['status'], "operational")

    def test_create_checklist_template_item_invalid_equipment_id(self):
        token = self._get_auth_token()
        template_data = {
            "name": "Test Template Invalid Equip",
            "type": "daily",
            "items": [
                {"item_description": "Check item with non-existent equipment", "equipment_id": 99999} # Assuming 99999 does not exist
            ]
        }
        response = self.client.post('/api/checklist-templates',
                                    headers={'x-access-token': token},
                                    data=json.dumps(template_data),
                                    content_type='application/json')
        self.assertEqual(response.status_code, 400, response.get_data(as_text=True))
        self.assertIn("Equipment with ID 99999 not found", response.get_data(as_text=True))

    def test_submit_checklist_item_invalid_equipment_id(self):
        token = self._get_auth_token(username="submitinvaliduser", password="password")
        # Create a valid template first
        template_data = {
            "name": "Valid Template For Invalid Item", "type": "daily",
            "items": [{"item_description": "A valid item description"}]
        }
        template_response = self.client.post('/api/checklist-templates', headers={'x-access-token': token}, data=json.dumps(template_data), content_type='application/json')
        template_id = json.loads(template_response.get_data(as_text=True))['id']

        checklist_data = {
            "checklist_template_id": template_id,
            "items": [
                {
                    "item_description_from_template": "A valid item description",
                    "status": "checked",
                    "equipment_id": 99999 # Assuming 99999 does not exist
                }
            ]
        }
        response = self.client.post('/api/checklists',
                                    headers={'x-access-token': token},
                                    data=json.dumps(checklist_data),
                                    content_type='application/json')
        self.assertEqual(response.status_code, 400, response.get_data(as_text=True))
        self.assertIn("Equipment with ID 99999 not found for an item", response.get_data(as_text=True))

    def test_get_nonexistent_equipment_history(self):
        token = self._get_auth_token()
        response = self.client.get('/api/equipment/99999/history', headers={'x-access-token': token}) # Assuming 99999 does not exist
        self.assertEqual(response.status_code, 404) # Or appropriate error for not found

    def test_get_nonexistent_checklist_details(self):
        token = self._get_auth_token()
        response = self.client.get('/api/checklists/99999', headers={'x-access-token': token}) # Assuming 99999 does not exist
        self.assertEqual(response.status_code, 404)

    def test_get_checklist_details_unauthorized(self):
        # User 1 creates a checklist
        token1 = self._get_auth_token(username="user1history", password="password")
        template_data = {"name": "User1 Template", "type": "daily", "items": [{"item_description": "Item 1"}]}
        template_response = self.client.post('/api/checklist-templates', headers={'x-access-token': token1}, data=json.dumps(template_data), content_type='application/json')
        template_id = json.loads(template_response.get_data(as_text=True))['id']
        checklist_data = {"checklist_template_id": template_id, "items": [{"item_description_from_template": "Item 1", "status": "ok"}]}
        submit_response = self.client.post('/api/checklists', headers={'x-access-token': token1}, data=json.dumps(checklist_data), content_type='application/json')
        checklist_id = json.loads(submit_response.get_data(as_text=True))['id']

        # User 2 (different user) tries to access it
        token2 = self._get_auth_token(username="user2history", password="password")
        response = self.client.get(f'/api/checklists/{checklist_id}', headers={'x-access-token': token2})
        self.assertEqual(response.status_code, 403)
        self.assertIn("Not authorized to view this checklist", response.get_data(as_text=True))

    # Consider adding tests for PUT/DELETE on ChecklistTemplates if those were implemented
    # For now, the instructions mentioned "if time permits", so focusing on core functionality.

    def test_create_equipment_missing_name(self):
        token = self._get_auth_token()
        response = self.client.post('/api/equipment',
                                   headers={'x-access-token': token},
                                   data=json.dumps({'category': 'SCBA'}), # Missing name
                                   content_type='application/json')
        self.assertEqual(response.status_code, 400)
        self.assertIn('Equipment name is required', response.get_data(as_text=True))

    def test_create_checklist_template_missing_fields(self):
        token = self._get_auth_token()
        # Missing 'type'
        template_data_no_type = {"name": "Incomplete Template", "items": [{"item_description": "Test"}]}
        response = self.client.post('/api/checklist-templates',
                                    headers={'x-access-token': token},
                                    data=json.dumps(template_data_no_type),
                                    content_type='application/json')
        self.assertEqual(response.status_code, 400)
        self.assertIn('Missing required fields: name, type, items', response.get_data(as_text=True))

        # Missing 'items'
        template_data_no_items = {"name": "Incomplete Template", "type": "daily"}
        response = self.client.post('/api/checklist-templates',
                                    headers={'x-access-token': token},
                                    data=json.dumps(template_data_no_items),
                                    content_type='application/json')
        self.assertEqual(response.status_code, 400)
        self.assertIn('Missing required fields: name, type, items', response.get_data(as_text=True))
        
        # Missing 'item_description' in one of the items
        template_data_missing_item_desc = {
            "name": "Template With Bad Item", 
            "type": "daily",
            "items": [{"expected_status": "Full"}] # Missing item_description
        }
        response = self.client.post('/api/checklist-templates',
                                    headers={'x-access-token': token},
                                    data=json.dumps(template_data_missing_item_desc),
                                    content_type='application/json')
        self.assertEqual(response.status_code, 400)
        self.assertIn('item_description is required for all items', response.get_data(as_text=True))

    def test_submit_checklist_missing_fields(self):
        token = self._get_auth_token(username="submitcheckuser", password="password")
        # Create a template first
        template_data = {"name": "Test Submit Template", "type": "daily", "items": [{"item_description": "Test Item"}]}
        template_response = self.client.post('/api/checklist-templates', headers={'x-access-token': token}, data=json.dumps(template_data), content_type='application/json')
        template_id = json.loads(template_response.get_data(as_text=True))['id']

        # Missing 'items'
        checklist_data_no_items = {"checklist_template_id": template_id}
        response = self.client.post('/api/checklists',
                                    headers={'x-access-token': token},
                                    data=json.dumps(checklist_data_no_items),
                                    content_type='application/json')
        self.assertEqual(response.status_code, 400)
        self.assertIn('Missing checklist_template_id or items', response.get_data(as_text=True)) # Message might be slightly different based on your specific check order

        # Missing 'item_description_from_template' in an item
        checklist_data_bad_item = {
            "checklist_template_id": template_id,
            "items": [{"status": "checked"}] # Missing item_description_from_template
        }
        response = self.client.post('/api/checklists',
                                    headers={'x-access-token': token},
                                    data=json.dumps(checklist_data_bad_item),
                                    content_type='application/json')
        self.assertEqual(response.status_code, 400)
        self.assertIn('item_description_from_template and status are required for all checklist items', response.get_data(as_text=True))

        # Missing 'status' in an item
        checklist_data_bad_item_status = {
            "checklist_template_id": template_id,
            "items": [{"item_description_from_template": "Test Item"}] # Missing status
        }
        response = self.client.post('/api/checklists',
                                    headers={'x-access-token': token},
                                    data=json.dumps(checklist_data_bad_item_status),
                                    content_type='application/json')
        self.assertEqual(response.status_code, 400)
        self.assertIn('item_description_from_template and status are required for all checklist items', response.get_data(as_text=True))

    def test_get_nonexistent_equipment(self):
        token = self._get_auth_token()
        response = self.client.get('/api/equipment/99999', headers={'x-access-token': token})
        self.assertEqual(response.status_code, 404)

    def test_update_nonexistent_equipment(self):
        token = self._get_auth_token()
        response = self.client.put('/api/equipment/99999',
                                   headers={'x-access-token': token},
                                   data=json.dumps({'name': 'New Name'}),
                                   content_type='application/json')
        self.assertEqual(response.status_code, 404)

    def test_delete_nonexistent_equipment(self):
        token = self._get_auth_token()
        response = self.client.delete('/api/equipment/99999', headers={'x-access-token': token})
        self.assertEqual(response.status_code, 404)

    def test_get_nonexistent_checklist_template(self):
        token = self._get_auth_token()
        response = self.client.get('/api/checklist-templates/99999', headers={'x-access-token': token})
        self.assertEqual(response.status_code, 404)
