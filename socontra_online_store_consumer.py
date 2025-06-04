# Socontra consumer AI agent template that commercially transacts with Web Agent online stores,
# such as the Shopify Web Agent. 
# This template is aimed to be generic to transact with any online store, beyond Shopify.

# Refer protocol template:
# - protocol_templates/online_stores/socontra_transact_store_protocol_consumer.py

# Also see the overview and tutorial on the socontra.com web site, comments in socontra_demo_9.py file,
# and the 'transact' protocol diagram in file Socontra service protocols.pdf.


from socontra.socontra import Socontra
from protocol_templates import  socontra_main_protocol
from protocol_templates.online_stores import  socontra_transact_store_protocol_consumer
import config

socontra = Socontra()
socontra.add_protocol(socontra_main_protocol)
socontra.add_protocol(socontra_transact_store_protocol_consumer)


if __name__ == '__main__':

    # Enter your credentials in the config.py file.
    client_public_id = config.client_public_id
    client_security_token = config.client_security_token

    consumer_agent = client_public_id + ':' + '<online_store_consumer_agent_here>'

    # Connect (and register if not already) the agent to the Socontra Network, to allow it to message, interact and transact with other agents.
    # Credentials for each new agent to connect back to the Socontra Network are stored in folder socontra/database.
    socontra.connect_socontra_agent(agent_data={
            'agent_name': consumer_agent,
            'client_security_token': client_security_token,
            'human_password': 'human_password_for_agent_here',
        }, clear_backlog = True,
        # Enter the agent's human owner data here, which is used in the automated commercial transaction process.
        agent_owner_data={
            'company_name': 'Consumer App',
            'first_name': 'John',
            'last_name': 'Doe',
            'address_line_one': '1 Consumer Street',
            'address_line_two': '',
            'city': 'San Francisco',
            'state_province': 'California',
            'zip_postal_code': '95016',
            'country': 'US',            # Use iso2 CountryCode in countries+states+cities.json (& https://shopify.dev/docs/api/storefront/latest/enums/countrycode)
            'email': 'example@email.com',
            'mobile_number': '+16135551111',
            'date_of_birth_year': 2000, # int
            'date_of_birth_month': 1,    # int
            'date_of_birth_day': 1,      #int
        })

    # Specify the distribution list of agent to send the service request to, using groups and regions.
    # See demo 6, 7 (part 1 to 3) and 8 for more info on groups and regions.
    # The distribution list specifies the public groups related to the product request sent out by this consumer agent.
    # The groups are listed in file: data/socontra_public_groups.json. These are based on Yelp business categories. Consistency 
    # with Yelp helps the agent or agent owner utilize Yelp to verify the store's credibility.
    # Regions are specified by 'country', 'state' and 'city', and must use the names in file data/countries+states+cities.json 
    # (which is from https://github.com/dr5hn/countries-states-cities-database/tree/master).
    # The agent can also use socontra.search_groups() to find standard 'socontra' or user created public groups of interest
    # (see demo 7 part 3).
    distribution_list = {
            # Specify public groups that the consumer agent whats to distribute 
            # Values for 'group_scope' are: 'direct' (specified group only), 'local' (includes sub-groups), 
            #            'global' (includes sub-groups and parent groups), and 'exclusive' (includes parent groups).
             'groups' :[{
                            'group_name' : [
                                                "socontra",
                                                "Restaurants",
                                                "Australian",
                            ],
                            'group_scope': 'local',   
                        },
                        {
                            'group_name' : [
                                                "socontra",
                                                "Restaurants",
                                                "Italian",
                                                "Abruzzese",
                            ],
                            'group_scope': 'local',   
                        }
                    ],

             'regions': [
                    {'country': 'US'},   # Request goods and services from Web Agent online stores across the whole country
                    {'country': 'US', 'state': 'CA'},   # Request goods and services from any Web Agent online stores across a state
                    {'country': 'US', 'state': 'CA', 'city': 'Los Angeles'},   # Request goods and services locally within a region/city.
                ]
            }

    # Define the task - or 'shopping list'. 
    task={'task': [
                    {'product_search_query': '<product 1 search query>',
                    'quantity': 1,
                    'number_proposals': 3}, # Number of search results. 3 is a good balance.
                    {'product_search_query': '<product 2 search query>',
                    'quantity': 1,
                    'number_proposals': 3},
                    {'product_search_query': '<product 3 search query>',
                    'quantity': 2,
                    'number_proposals': 3}
                    ]
    }

    # Timeout in seconds for receiving non-binding proposals (search results) to achieve the task. Service protocols rely on timeouts 
    # because in an open decentralized world where agents are autonomous and self-interested, responses to requests and messages are 
    # not guaranteed.
    proposal_timeout = 20

    # Timeout in seconds for receiving binding offers from suppliers. 
    invite_offer_timeout = 20

    # For the Socontra transact protocol, we use a central orchestrator, contained in the protocol template file
    # protocol_templates/online_stores/socontra_transact_store_protocol_consumer.py.
    socontra.transact_orchestrator_consumer(consumer_agent, task, distribution_list, proposal_timeout, invite_offer_timeout)

    
