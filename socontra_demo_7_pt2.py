# Socontra demo 7 part 2
# We demonstrate group geographical regions, enabling agent request to be restricted by both groups (representing area of interest
# or business category) and geographical region (e.g. the region which the agent services). 
# Ensure that demo 6 and 7 are run first, where we created some open public groups.

# Agents that are members of groups can specify geographical regions that it services, to further restrict or target
#   communications or task/purchase requests from other agents. Likewise, agents can use regions in distribution lists
#   to ensure that the messages are only sent to relevant agents in the region of interest.
# Regions have the format:
#   regions = [
#               {'country': <country>, 'state': <state>, 'city': <city>},
#               {'country': <country>, 'state': <state>},
#               {'country': <country>},
#               {...}, ...
#             ]

# The region names for country, state and city must be consistent with the file data/countries+states+cities.json
# -> source is https://github.com/dr5hn/countries-states-cities-database/tree/master

# Country is mandatory, however state and city are not.
# If no regions are specified, either by the sender or receiver (agent group member), all agents will be sent the message by the sender.
# If regions are specified, by both sender and receiver, then Socontra will check conduct a region matching to decide whether to send the 
# message between sender and receiver, which is:
#   - Check if countries match, and if states are not specified by either agent, then send the message.
#   - If states are specified by both sender and receiver, then check if states match, and
#       if cities are not specified by either agent, then send the message.
#   - If cities are specified by both sender and receiver, then check if cities match, and if so, send the message,
#       and if not, don't send the message.

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
    # This hierarchy can be viewed using command get_sub_groups(self, agent_name: str, group_name_path: list[str])
    response = socontra.get_sub_groups(group_admin_agent, [client_public_id, 'Travel'])
    print('\n----------------------------------Travel hierarchy of groups ----------------------------------------------\n')
    pprint(response.http_response)

    # Each of the agents now specify their regions of service.
    # We won't specify regions for group_admin_agent - so it will receive all messages to the group.
    socontra.add_region_group(flight_agent, [client_public_id, 'Travel', 'Flight'],
                              [
                                  {'country': 'US'},    # United States (US)
                                  {'country': 'CA'},    # Canada
                                  {'country': 'AU'},    # Australia
                              ])
    
    socontra.add_region_group(hotel_agent, [client_public_id, 'Travel', 'Hotel'],
                              [
                                  {'country': 'US', 'state': 'CA'},     # US, California
                                  {'country': 'US', 'state': 'AZ'},     # US, Arizona
                                  {'country': 'US', 'state': 'NV'}      # US, Nevada
                              ])
    
    socontra.add_region_group(apartment_agent, [client_public_id, 'Travel', 'Hotel', 'Apartment'],
                              [
                                  {'country': 'US', 'state': 'CA', 'city': 'San Francisco'},    # US, California, San Francisco
                                  {'country': 'US', 'state': 'CA', 'city': 'Anaheim'}           # US, California, Anaheim
                              ])
    
    socontra.add_region_group(resort_agent, [client_public_id, 'Travel', 'Hotel', 'Resort'],
                              [
                                  {'country': 'US', 'state': 'CA', 'city': 'Palm Springs'},     # US, California, Palm Springs
                                  {'country': 'US', 'state': 'CA', 'city': 'Los Angeles'},      # US, California, Los Angeles
                                  {'country': 'US', 'state': 'NV', 'city': 'Las Vegas'},        # US, California, Las Vegas
                              ])

    time.sleep(1)

    # The travel_customer can transact with these agents based on regions of interest.
    # To demonstrate, we will use message protocol in demo 1 (ignore unrelated message response from the agents).

    # prepare a distribution list for the travel_customer to include all agents in all groups (i.e. sub-groups)
    # in the 'Travel' group. So the only restriction for agents that are members of these groups are region.
    distribution_list = {
            # Specify groups that the agent is a member of to communicate with the groups' members.
            # Values for 'group_scope' are: 'direct' (specified group only), 'local' (includes sub-groups), 
            #            'global' (includes sub-groups and parent groups), and 'exclusive' (includes parent groups).
             'groups' :[
                        {
                            'group_name' : [client_public_id, 'Travel'],
                            'group_scope': 'global', 
                        },
                    ],

            # List the region(s) relevant to the required services. This is populated in the code example below.
            #'regions': [
            #               {'country': <country>, 'state': <state>, 'city': city}
            #       ],

            # List names of agent names for direct agent-to-agent communication. The sender agent must be 'connected to' recipient agents. 
            # 'direct' : [],
        }


    # First send a message to include all regions. Do this by not specifying any regions at all.
    print('\n----------------------------All agents for all regions----------------------------------------------------\n')
    message="Hi there! Can you tell me about your travel deals."
    socontra.new_message(agent_name=travel_customer, distribution_list=distribution_list, message=message, protocol='socontra')
    time.sleep(1)


    # Now limit the regions to 'US'. Since all the agents operate in the US, the message will be sent to all agents.
    distribution_list['regions'] = [
        {'country': 'US'}
    ]
    
    print('\n------------------------------Agents that service the United States--------------------------------------------------\n')
    message="Hi there! Can you tell me about your travel deals in the USA."
    socontra.new_message(agent_name=travel_customer, distribution_list=distribution_list, message=message, protocol='socontra')
    time.sleep(1)

    # travel_customer now wants to narrow the search to agents in Nevada. Agents that cover Nevada or the whole
    # of the USA will be included.
    distribution_list['regions'] = [
        {'country': 'US', 'state': 'NV'}
    ]
    
    print('\n--------------------------------Agent that service Nevada------------------------------------------------\n')
    message="Hi there! Can you tell me about travel deals in Nevada."
    socontra.new_message(agent_name=travel_customer, distribution_list=distribution_list, message=message, protocol='socontra')
    time.sleep(1)


    # Lastly, travel_customer wants to explore travel deals in Anaheim. Agent that cover US, CA (California), or Anaheim 
    # specifically will be included.
    distribution_list['regions'] = [
        {'country': 'US', 'state': 'CA', 'city': 'Anaheim'}
    ]
    
    print('\n----------------------------------Agent that service Anaheim----------------------------------------------\n')
    message="Hi there! Can you tell me about travel deals in Anaheim."
    socontra.new_message(agent_name=travel_customer, distribution_list=distribution_list, message=message, protocol='socontra')
    time.sleep(2)

    # Agents can view regions they have specified for groups they are members of.
    response = socontra.get_region_group(hotel_agent, [client_public_id, 'Travel', 'Hotel'])
    print('\n----------------------------------Get Hotel agent configured regions----------------------------------------------\n')
    pprint(response.http_response)

    # Agents can also delete regions for groups they are members of.
    response = socontra.delete_region_group(hotel_agent, [client_public_id, 'Travel', 'Hotel'], [{'country': 'US', 'state': 'AZ'}])
    print('\n----------------------------------Hotel agent deletes Arizona as a region to service---------------------------------\n')
    pprint(response.http_response)

    # Get and print out the updated list of regions for the group.
    response = socontra.get_region_group(hotel_agent, [client_public_id, 'Travel', 'Hotel'])
    pprint(response.http_response)
    
 
    