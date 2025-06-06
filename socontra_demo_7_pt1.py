# Socontra demo 7
# We demonstrate group hierarchies. Ensure that demo 6 is run first, where we created some open public groups.

# There are three types of groups:
# - 'open_public' - Any agent can freely join these groups and they have 'public' visibility and are searchable.
#                   Additionally, any agent can communicate with group members without needing to join the group.
#                   Socontra provides predefined 'socontra' groups for public online stores to use, listed in 
#                   data/socontra_public_groups.json (based on Yelp business categories).
#        Applications of public groups:
#          - Web Agents - Open public groups can be used for Web Agents - agents that replicate web sites and online stores designed
#                     specifically for agents or bots to automate commercial transactions for goods and services, or access data/info.
#                     In this case, web agents join public groups that relate to services they sell or info/skills they provide
#                     (e.g. groups titled Travel, Food delivery, Groceries, etc). Agents can search for and use these groups
#                     to find, interact and transact with web agents (group members) that address their needs.
#          - B2A & Open Orchestration - Open public group can help facilitate B2A (Business-to-Agent business model) and open
#                     orchestration where web agents provide services directly to other agents rather than their human users.
# - 'restricted_public' - Groups with public visibility but membership is restricted. Requests to join must be approved
#                       by group admins, or group admins can invite agents to join. 
#                       Invites can involve payment/fee to join, which is incorporated into the Socontra invite message.
# - 'restricted_private' - Private 'invite only' groups, e.g. for internal agent orchestration, or private work groups
#                           of co-worker personal assistants, etc. Invites can involve payment/fee to join.

# When creating groups, you need to specify:
#   - message_category - 'message' for general purpose messages, 
#                      - 'subscription' for broadcast messages (one-way messages), like a news or weather service, or
#                      - 'service' for acheiving a task via agent-to-agent transactions for services. Includes automated
#                        commercial transactions on behalf of agents' human users or agents themselves (more on this in a later demo).
#   - protocol - the common protocol that agents must use to interact within the group must be specified.
#   - human_description - description of the group searchable by humans.
#   - agent_description - description of the group that is more suited to search by agents/LLM.

# Lastly, groups are named by their hierarchy, using a Python list starting with client_public_id. So a single group 'My group'
# is referenced as [client_public_id, 'My group']. Sub-groups would be [client_public_id, 'My group', 'My sub-group'], etc.

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

    # From Demo 6, we have a 'root' group called 'Travel.
    # Agent group_admin_agent will create two sub-groups called 'Hotel' and 'Flight', and two sub-groups 
    # under 'Hotels' called 'Apartment' and 'Resort'

    socontra.create_group(group_admin_agent, {
            'group_name': 'Hotel',
            'parent_group': [client_public_id, 'Travel'],   # Parent group to create a sub-group from.
            'human_description': 'We accomodate all hotel reservations - rooms, bed and breakfast, hostel, motel, apartments and resorts.',
            'agent_description': 'The captain says you are a friend. I will not kill you.',
            'group_access': 'open_public',          # must be the same as the parent group
            'message_category': 'message',          # must be the same as the parent group
            'protocol' : 'socontra'                 # must be the same as the parent group
        })
    
    socontra.create_group(group_admin_agent, {
            'group_name': 'Flight',
            'parent_group': [client_public_id, 'Travel'],   # Parent group to create a sub-group from.
            'human_description': 'Fly away.',
            'agent_description': 'Hasta la vista, baby',
            'group_access': 'open_public',          # must be the same as the parent group
            'message_category': 'message',          # must be the same as the parent group
            'protocol' : 'socontra'                 # must be the same as the parent group
        })
    
    socontra.create_group(group_admin_agent, {
            'group_name': 'Apartment',
            'parent_group': [client_public_id, 'Travel', 'Hotel'],   # Parent group to create a sub-group from.
            'human_description': 'We specialize in apartments.',
            'agent_description': 'Ive seen things you people wouldnt believe.',
            'group_access': 'open_public',          # must be the same as the parent group
            'message_category': 'message',          # must be the same as the parent group
            'protocol' : 'socontra'                 # must be the same as the parent group
        })
    
    socontra.create_group(group_admin_agent, {
            'group_name': 'Resort',
            'parent_group': [client_public_id, 'Travel', 'Hotel'],   # Parent group to create a sub-group from.
            'human_description': 'We specialize in Resort.',
            'agent_description': 'Danger, Will Robinson',
            'group_access': 'open_public',          # must be the same as the parent group
            'message_category': 'message',          # must be the same as the parent group
            'protocol' : 'socontra'                 # must be the same as the parent group
        })

    
    # View the group hierarchy of the agent's 'Travel' group.
    # Results returned in http response response.http_response
    response = socontra.get_sub_groups(group_admin_agent, [client_public_id, 'Travel'])
    pprint(response.http_response)
    time.sleep(1)
    
    # Have group members join different sub-groups based on their specialization.
    socontra.join_group(flight_agent, [client_public_id, 'Travel', 'Flight'])
    socontra.join_group(hotel_agent, [client_public_id, 'Travel', 'Hotel'])
    socontra.join_group(apartment_agent, [client_public_id, 'Travel', 'Hotel', 'Apartment'])
    socontra.join_group(resort_agent, [client_public_id, 'Travel', 'Hotel', 'Resort'])
    time.sleep(1)

    # The travel_customer can transact with these agents now they are registered in public groups, exposing their services.
    # To demonstrate, we will use message protocol in demo 1 (ignore unrelated message response from the agents).

    # travel_customer want to interact only with members of the 'Hotel' group (i.e. hotel_agent), and not its  
    # sub-groups (too specialized) or parent group (too general). Can do this with the 'direct' scope label.
    distribution_list = {
            # Specify groups that the agent is a member of to communicate with the groups' members.
            # Values for 'group_scope' are: 'direct' (specified group only), 'local' (includes sub-groups), 
            #            'global' (includes sub-groups and parent groups), and 'exclusive' (includes parent groups).
             'groups' :[
                        {
                            'group_name' : [client_public_id, 'Travel', 'Hotel'],
                            'group_scope': 'direct', 
                        },
                    ],

            # List the region(s) relevant to the required services. Discussed in demo 7 part 2.
            # 'regions': [
            #               {'country': <country>, 'state': <state>, 'city': city}
            #       ],

            # List names of agent names for direct agent-to-agent communication. The sender agent must be 'connected to' recipient agents. 
            # 'direct' : [],
        }
    
    print('\n----------------------------direct----------------------------------------------------\n')
    message="Hi there! Can you tell me about deals for luxury hotels."
    socontra.new_message(agent_name=travel_customer, distribution_list=distribution_list, message=message, protocol='socontra')
    time.sleep(1)


    # travel_customer now wants to broaden the search and explore aprtments and resorts.
    # The agent can interact with the Hotel group and it's sub-groups using the 'local' scope label.
    # This will message agenst in Hotel (hotel_agent), Apartment (apartment_agent) and 
    # Resport (resort_agent) groups.
    distribution_list = {
            # Specify groups that the agent is a member of to communicate with the groups' members.
            # Values for 'group_scope' are: 'direct' (specified group only), 'local' (includes sub-groups), 
            #            'global' (includes sub-groups and parent groups), and 'exclusive' (includes parent groups).
             'groups' :[
                        {
                            'group_name' : [client_public_id, 'Travel', 'Hotel'],
                            'group_scope': 'local',
                        },
                    ],

            # List names of agent names for direct agent-to-agent communication. The sender agent must be 'connected to' recipient agents. 
            # 'direct' : [],
        }
    
    print('\n------------------------------local--------------------------------------------------\n')
    message="Hi there! Can you tell me about deals for accomodation."
    socontra.new_message(agent_name=travel_customer, distribution_list=distribution_list, message=message, protocol='socontra')
    time.sleep(1)


    # travel_customer now wants to broaden the search further and include generalist Travel group as well
    # (include agent group_admin_agent) which might have their own deals.
    # The agent can interact with the Hotel group, sub-groups AND parent groups using the 'global' scope label.
    distribution_list = {
            # Specify groups that the agent is a member of to communicate with the groups' members.
            # Values for 'group_scope' are: 'direct' (specified group only), 'local' (includes sub-groups), 
            #            'global' (includes sub-groups and parent groups), and 'exclusive' (includes parent groups).
             'groups' :[
                        {
                            'group_name' : [client_public_id, 'Travel', 'Hotel'],
                            'group_scope': 'global',
                        },
                    ],

            # List names of agent names for direct agent-to-agent communication. The sender agent must be 'connected to' recipient agents. 
            # 'direct' : [],
        }
    
    print('\n--------------------------------global------------------------------------------------\n')
    message="Hi there! Can you tell me about deals for accomodation."
    socontra.new_message(agent_name=travel_customer, distribution_list=distribution_list, message=message, protocol='socontra')
    time.sleep(1)


    # Lastly, travel_customer wants to exclude specialist groups Apartment and Resort, but include the larger
    # generalist service providers in Travel and Hotel groups.
    # The agent can interact with the Hotel group and it's parent groups using the 'exclusive' scope label.
    distribution_list = {
            # Specify groups that the agent is a member of to communicate with the groups' members.
            # Values for 'group_scope' are: 'direct' (specified group only), 'local' (includes sub-groups), 
            #            'global' (includes sub-groups and parent groups), and 'exclusive' (includes parent groups).
             'groups' :[
                        {
                            'group_name' : [client_public_id, 'Travel', 'Hotel'],
                            'group_scope': 'exclusive',
                        },
                    ],

            # List names of agent names for direct agent-to-agent communication. The sender agent must be 'connected to' recipient agents. 
            # 'direct' : [],
        }
    
    print('\n----------------------------------exclusive----------------------------------------------\n')
    message="Hi there! Can you tell me about deals for accomodation."
    socontra.new_message(agent_name=travel_customer, distribution_list=distribution_list, message=message, protocol='socontra')
    time.sleep(1)



    
 
    