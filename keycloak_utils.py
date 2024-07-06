import requests
from django.conf import settings

keycloak_config = settings.KEYCLOAK_CONFIG

def get_keycloak_config_value(key, default=None):
    return keycloak_config.get(key, default)

class KeycloakAdmin:
    def __init__(self):
        self.server_url = get_keycloak_config_value('KEYCLOAK_SERVER_URL')
        self.username = get_keycloak_config_value('KEYCLOAK_USERNAME')
        self.password = get_keycloak_config_value('KEYCLOAK_PASSWORD')
        self.realm_name = get_keycloak_config_value('KEYCLOAK_REALM')
        self.client_id = get_keycloak_config_value('KEYCLOAK_CLIENT_ID')
        self.client_secret = get_keycloak_config_value('KEYCLOAK_CLIENT_SECRET_KEY')
        self.admin_token = None

    def get_admin_token(self):
        if not self.admin_token:
            token_url = f"{self.server_url}/realms/{self.realm_name}/protocol/openid-connect/token"
            data = {
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "grant_type": "password",
                "username": self.username,
                "password": self.password
            }
            response = requests.post(token_url, data=data)
            try:
                response.raise_for_status()
                self.admin_token = response.json().get('access_token')
            except requests.exceptions.HTTPError as e:
                print(f"HTTP Error while getting admin token: {e}")
                print("Response content:", response.text)
            except Exception as e:
                print(f"Unexpected error while getting admin token: {e}")
        return self.admin_token

    def create_user(self, email, password):
        create_user_url = f"{self.server_url}/admin/realms/{self.realm_name}/users"
        headers = {
            "Authorization": f"Bearer {self.get_admin_token()}",
            "Content-Type": "application/json"
        }
        user_data = {
            "username": email,
            "email": email,
            "enabled": True,
            "credentials": [{
                "type": "password",
                "value": password,
                "temporary": False
            }]
        }
        response = requests.post(create_user_url, headers=headers, json=user_data)
        try:
            response.raise_for_status()
            user_creation_response = response.json()
            print("User creation response:", user_creation_response)
            user_id = self.get_user_id_by_email(email)
            self.remove_required_actions(user_id)
            return user_creation_response
        except requests.exceptions.HTTPError as e:
            print(f"HTTP Error while creating user: {e}")
            print("Response content:", response.text)
        except Exception as e:
            print(f"Unexpected error while creating user: {e}")
        return None

    def get_user_id_by_email(self, email):
        users_url = f"{self.server_url}/admin/realms/{self.realm_name}/users"
        headers = {
            "Authorization": f"Bearer {self.get_admin_token()}",
            "Content-Type": "application/json"
        }
        response = requests.get(users_url, headers=headers, params={"email": email})
        response.raise_for_status()
        users = response.json()
        if users:
            return users[0]['id']
        return None

    def remove_required_actions(self, user_id):
        user_url = f"{self.server_url}/admin/realms/{self.realm_name}/users/{user_id}"
        headers = {
            "Authorization": f"Bearer {self.get_admin_token()}",
            "Content-Type": "application/json"
        }
        data = {
            "requiredActions": []
        }
        response = requests.put(user_url, headers=headers, json=data)
        try:
            response.raise_for_status()
            print(f"Required actions removed for user {user_id}")
        except requests.exceptions.HTTPError as e:
            print(f"HTTP Error while removing required actions: {e}")
            print("Response content:", response.text)
        except Exception as e:
            print(f"Unexpected error while removing required actions: {e}")



def generate_keycloak_token(email, password):
    token_url = f"{keycloak_config['KEYCLOAK_SERVER_URL']}/realms/{keycloak_config['KEYCLOAK_REALM']}/protocol/openid-connect/token"
    form = {
        "client_id": keycloak_config['KEYCLOAK_CLIENT_ID'],
        "client_secret": keycloak_config['KEYCLOAK_CLIENT_SECRET_KEY'],
        "grant_type": "password",
        "username": email,
        "password": password,
        "scope": "openid profile email"
    }

    try:
        response = requests.post(token_url, data=form, headers={"Content-Type": "application/x-www-form-urlencoded"})
        response.raise_for_status()
        token_response = response.json()
        return token_response
    except requests.RequestException as e:
        print(f"Error generating Keycloak token: {str(e)}")
        print("Response content:", response.text)
        raise Exception(f"Error generating Keycloak token: {str(e)}")





