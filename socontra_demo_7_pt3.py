# Socontra demo 7 part 3
# We demonstrate searching for public groups based on search terms.

# Pre-defined public groups with client_public_id = 'socontra' are based on Yelp business categories and intended to  
# to be used by Web Agents (online stores) wanting to sell goods and services. Consistency with Yelp business categories
# helps the AI agent or agent's owner to verify any Web Agent store's credibility via the Yelp website/platform.

# We utilize the simple message protocol in demo 1 (protocol_templates/message/socontra_message_protocol1.py).


from socontra.socontra import Socontra
from protocol_templates import  socontra_main_protocol
from protocol_templates.message import  socontra_message_protocol1
import config
import time
from pprint import pprint

socontra = Socontra()
socontra.add_protocol(socontra_main_protocol)
socontra.add_protocol(socontra_message_protocol1)


if __name__ == '__main__':

    # Enter your credentials in the config.py file.
    client_public_id = config.client_public_id
    client_security_token = config.client_security_token

    group_admin_agent = client_public_id + ':' + 'group_admin_agent'
    hotel_agent = client_public_id + ':' + 'hotel_agent'
    flight_agent = client_public_id + ':' + 'flight_agent'
    apartment_agent = client_public_id + ':' + 'apartment_agent'
    resort_agent = client_public_id + ':' + 'resort_agent'
    travel_customer = client_public_id + ':' + 'travel_customer'

    # Connect (and register if not already) the agent to the Socontra Network, to allow it to message, interact and transact with other agents.
    # Credentials for each new agent to connect back to the Socontra Network are stored in folder socontra/database.
    socontra.connect_socontra_agent(agent_data={
            'agent_name': group_admin_agent,
            'client_security_token': client_security_token,
            'human_password': 'human_password_for_agent_here',
        }, clear_backlog = True)
    
    socontra.connect_socontra_agent(agent_data={
            'agent_name': hotel_agent,
            'client_security_token': client_security_token,
            'human_password': 'human_password_for_agent_here',
        }, clear_backlog = True)
    
    socontra.connect_socontra_agent(agent_data={
            'agent_name': flight_agent,
            'client_security_token': client_security_token,
            'human_password': 'human_password_for_agent_here',
        }, clear_backlog = True)
    
    socontra.connect_socontra_agent(agent_data={
            'agent_name': apartment_agent,
            'client_security_token': client_security_token,
            'human_password': 'human_password_for_agent_here',
        }, clear_backlog = True)
    
    socontra.connect_socontra_agent(agent_data={
            'agent_name': resort_agent,
            'client_security_token': client_security_token,
            'human_password': 'human_password_for_agent_here',
        }, clear_backlog = True)
    
    socontra.connect_socontra_agent(agent_data={
            'agent_name': travel_customer,
            'client_security_token': client_security_token,
            'human_password': 'human_password_for_agent_here',
        }, clear_backlog = True)

    # Refer Demo 6 and 7 to which created the open_public 'Travel' group hierarchy, with
    # two sub-groups called 'Hotel' and 'Flight', and two sub-groups 
    # under 'Hotels' called 'Apartment' and 'Resort'
    # flight_agent, hotel_agent, apartment_agent, and resort_agent join the
    # 'Flight', 'Hotel', 'Apartment' and 'Resort' resort groups, respectively.
    
    # The travel_customer wants to find all public groups by client_public_id relating to resorts, with the string 'resort' in 
    # the group_name, human_description or agent_description. Requires an exact match, and is case insensitive.
    # A maximum of 350 results will be returned.
    response = socontra.search_groups(travel_customer, client_public_id=client_public_id, group_name_term='resort', human_description_term='resort', agent_description_term='resort')
    print('\n----------------------------Search results----------------------------------------------------\n')
    pprint(response.http_response)

    # The groups can be used to add to the distribution list for sending a message or service request.
    # LLMs can analyze the list to select most suitable groups to include in the distribution list.
    distribution_list = {'groups': []}

    for a_searched_group in response.http_response:
        group_to_add = {
            'group_name': a_searched_group['group_name'],
            'group_scope': 'direct'     # Only message agents in the group, and not parent or sub-groups.
        }
        distribution_list['groups'].append(group_to_add)

    print('\n----------------------------Message searched agents----------------------------------------------------\n')
    message="Hi there! Can you tell me about your travel deals for resorts."
    socontra.new_message(agent_name=travel_customer, distribution_list=distribution_list, message=message, protocol='socontra')
    time.sleep(3)

    # You can search for pre-defined public groups to be used by Web Agent online stores, by setting client_public_id='socontra'.
    response = socontra.search_groups(travel_customer, client_public_id='socontra', group_name_term='resort', human_description_term='resort', agent_description_term='resort')
    print('\n----------------------------Public Web Agent online stores search results----------------------------------------------------\n')
    pprint(response.http_response)

 
    