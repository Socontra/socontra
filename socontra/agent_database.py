# Database for agents - which will be stored on any device, e.g. computers, phones, etc. 
# So needs to be local and light weight. Since data is small and relatively static, will store in files
# to avoid having extra installs of databases etc.

from socontra.security import encrypt_password, decrypt_password, generate_password
import time
import json 
import time
import os
import config 

class AgentDatabase:

    def __init__(self):
        self.socontra_network_url = config.socontra_network_url
        self.socontra_network_port = config.socontra_network_port
        
        self.socontra_network_urlport = f'{self.socontra_network_url}:{str(self.socontra_network_port)}'
        
        self.agent_data = {
            'agent_name': None,
            'encrypted_client_security_token': None,
            'encrypted_agent_password': None,  # This is a password that the agent generates and will use to access the Socontra network.
            'created_at': None,
            'updated_at': None,
            'agent_password_updated_at': None
        }
        
        # Store optional agent owner data locally. This info is also on the Socontra Network.
        self.agent_owner_data = {
            # Agent authorized owner: each agent must be associated with a human or company user that is responsible for agent and its actions when in use.
            'company_name': None,
            'first_name': None,
            'last_name': None,
            'address_line_one': None,
            'address_line_two': None,
            'city': None,
            'state_province': None,
            'zip_postal_code': None,
            'country': None,
            'email': None,
            'mobile_number': None,
            'date_of_birth_year': None, # int
            'date_of_birth_month': None,    # int
            'date_of_birth_day': None,      #int
            'created_at': None,
            'updated_at': None,
        }

        self.agent_owner_transaction_config = {
            'currency': None,  # Optional     # If not provided, then will use currency of supplier agents.
            # Automated payment thresholds - these can be set to zero to ensure human user always authorizes the transaction.
            'automated_limit_per_day': None,    # float
            'automated_limit_per_transaction': None,    # float
            'created_at': None,
            'updated_at': None,
        }

        self.socontra_access_token = None

        # TODO - Agent payment info.


    def store_register_agent_details(self, agent_data: dict, agent_owner_data: dict = None, agent_owner_transaction_config: dict = None):
        # Store the info when registering agent.

        # Store agent_data first. Do this one by one as small list and some elements need processing (excryption/hashing).
        self.agent_data['agent_name'] = agent_data['agent_name']
        self.agent_data['encrypted_client_security_token']= encrypt_password(agent_data['client_security_token']), 
        self.agent_data['encrypted_agent_password']= encrypt_password(agent_data['agent_password']),
        self.agent_data['created_at']= time.time()
        self.agent_data['agent_password_updated_at']= time.time()

        # Lets save this info to a file, as we want this to persist.
        self.store_data_to_file(self.agent_data, 'agent_data')

        # Now set the rest of the agent owner data, if defined.
        if agent_owner_data:
            for k, v in agent_owner_data.items():
                self.agent_owner_data[k] = v
        
        self.agent_owner_data['created_at']= time.time()

        # Lets save this info to a file, as we want this to persist.
        self.store_data_to_file(self.agent_owner_data, 'agent_owner_data')

        if agent_owner_transaction_config:
            for k, v in agent_owner_transaction_config.items():
                self.agent_owner_transaction_config[k] = v

        self.agent_owner_transaction_config['created_at']= time.time()

        # Lets save this info to a file, as we want this to persist.
        self.store_data_to_file(self.agent_owner_transaction_config, 'agent_owner_transaction_config')

    def update_agent_data(self, data_to_edit: dict):
        # A general function taking in a dict of edits provided to the Socontra Network to make about this agent.
        # This function will just go through the edit list and make the changes.

        if data_to_edit:
            agent_data = False
            agent_owner_data = False
            agent_owner_transaction_config = False
            
            for k, v in data_to_edit.items():
                if v != None: # Make sure an item wanting to edit and not None
                    # Now need to make the edit. However, not sure which database. So find the database and make the edit.
                    if k in self.agent_data:
                        self.agent_data[k] = v
                        agent_data = True
                    elif k in self.agent_owner_data:
                        self.agent_owner_data[k] = v
                        agent_owner_data = True
                    elif k in self.agent_owner_transaction_config:
                        self.agent_owner_transaction_config[k] = v
                        agent_owner_transaction_config = True

            # Now  save the edited database to file.
            if agent_data:
                self.store_data_to_file(self.agent_data, 'agent_data')
            if agent_owner_data:
                self.store_data_to_file(self.agent_owner_data, 'agent_owner_data')
            if agent_owner_transaction_config:
                self.store_data_to_file(self.agent_owner_transaction_config, 'agent_owner_transaction_config')

    def store_data_to_file(self, data: dict, filename_key: str):
        # Will store the data to a file in folder 'database'.
        
        # Set the updated field to current time.
        data['updated_at'] = time.time()
        agent_name =self.agent_data['agent_name']
        agent_name_filesafe = self.convert_to_filename_safe_string(agent_name)
        filename = f'socontra/database/{agent_name_filesafe}-{filename_key}.txt'
       
        try:
            with open(filename, 'w') as data_to_store: 
                data_to_store.write(json.dumps(data))
        except OSError:
            print('Unable to save data to file', data)

    def convert_to_filename_safe_string(self, string: str):
        return "".join(i if i not in "\/:*?<>|" else "_" for i in string )

    def read_data_from_file(self, filename_key: str, agent_name: str =None):
        # Will read a dict from file and return it as a dict.
        if not agent_name:
            agent_name =self.agent_data['agent_name']
        
        agent_name_filesafe = self.convert_to_filename_safe_string(agent_name)
       
        filename = f'socontra/database/{agent_name_filesafe}-{filename_key}.txt'

        # If the file does not exist, dont try and open it.
        if not os.path.isfile(filename):
            return False

        try:
            with open(filename) as f: 
                data = f.read()
            return json.loads(data)
        except OSError:
            return False
    
    def does_database_exist(self, agent_name: str =None, filename_key: str = None):
        # Will check if a file containing the agent info exists (i.e. the file is our persistent database, which we read into 
        # memory - our object vars).
        
        # If no filename, then check if the primary/mandatory agent data base exists - which demostrates that the agent exists.
        if not filename_key:
            filename_key = 'agent_data'
        
        if not agent_name:
            agent_name =self.agent_data['agent_name']
        
        agent_name_filesafe = self.convert_to_filename_safe_string(agent_name)

        filename = f'socontra/database/{agent_name_filesafe}-{filename_key}.txt'

        return os.path.isfile(filename)

    def restart_agent_database(self):
        # If the agent gets shut down, then we will want to get all the data in the database (files) back into memory for quick access.
        self.agent_data = self.read_data_from_file(self, 'agent_data')
        self.agent_owner_data = self.read_data_from_file(self, 'agent_owner_data')
        self.agent_owner_transaction_config = self.read_data_from_file(self, 'agent_owner_transaction_config')

    def store_socontra_access_token(self, access_token: str):
        # Will store the Socontra access token - in memory only. 
        self.socontra_access_token = access_token

    def get_socontra_access_token(self):
        # Will return the Socontra access token - from memory only. 
        return self.socontra_access_token

    def get_client_security_token(self):
        # Will return the client security token.
        return decrypt_password(self.agent_data['encrypted_client_security_token'])
    
    def update_client_security_token(self, client_security_token: str, save_to_file=True):
        # Will update the client security token - used to allow all the agenst from the agent's developers to access the Socontra network.
        self.agent_data['encrypted_client_security_token']= encrypt_password(client_security_token),

        # Now save to file.
        if save_to_file:
            self.store_data_to_file(self.agent_data, 'agent_data')
    
    def get_agent_password(self):
         # Will return the agent password to access the Socontra Network.
        return decrypt_password(self.agent_data['encrypted_agent_password'])
    
    def update_agent_password(self, agent_password: str, save_to_file=True):
        # Will update the agent password - used for authentication and get an access token from the Socontra Network, to allow
        # this agent to comminicate and send messages to the Socontra Network and thus interact/transact with other agents.
        self.agent_data['agent_password_updated_at'] = time.time()      # datetime.datetime.now(datetime.timezone.utc)
        self.agent_data['encrypted_agent_password']= encrypt_password(agent_password)

        # Now save to file.
        if save_to_file:
            self.store_data_to_file(self.agent_data, 'agent_data')

    def last_time_updated_password_hours(self):
        # Will return in hours the last time the password was changed - as it should be changed regularly. TODO
        time_diff =  time.time() - self.agent_data['agent_password_updated_at']
        return time_diff.total_seconds() / (60*60)
    
    def create_new_agent_password(self, password_length: int):
        # Will create a new agent password to be used to access the Socontra Network.
        return generate_password(password_length)

    def get_agent_name(self):
        return self.agent_data['agent_name']
        

    def recreate_agent_if_exists(self, agent_data):
        # Will check if agent_data is stored in the database (database folder), and if so, will create the agent.

        if self.does_database_exist(agent_data['agent_name']):

            # Read in the agent_data.
            agent_data_from_file = self.read_data_from_file('agent_data', agent_data['agent_name'])

            if agent_data_from_file:
                # Agent data read in ok. Read remaining data.
                self.agent_data = agent_data_from_file
                self.agent_owner_data = self.read_data_from_file('agent_owner_data')
                self.agent_owner_transaction_config = self.read_data_from_file('agent_owner_transaction_config')
                return True
            else:
                # Issue reading in the database primary file 'agent_data'
                return False
        else:
            # Agent does not exist. Possibly not yet registered.
            return False
        
    
