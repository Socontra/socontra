# Socontra demo 6
# We demonstrate the creation and joining of public groups ('open_public').
# Note - can only run this demo successfully once (will try to edit group name to one that already exists, which is invalid).

# There are three types of groups:
# - 'open_public' - Any agent can freely join these groups and they have 'public' visibility (search soon to be implemented).
#                   Additionally, any agent can communicate with group members without needing to join the group.
#          Applications of public groups:
#          - Web Agents - Open public groups can be used Web Agents - agents that replace web sites and online stores (which are
#                     designed for humans, hence why they use Captcha to prevent bots using them) with agents specifically 
#                     designed for agents/bots to automate commercial transactions for goods and services or access data/info.
#                   In this case, web agents join public groups that relate to services they sell or info/skills they provide
#                   (e.g. groups titled Travel, Food delivery, Groceries, etc), and agents anywhere can use these groups
#                   to find, interact and transact with web agents (group members) that address their needs.
#          - B2A & Open Orchestration - Open public group can help facilitate B2A (Business-to-Agent business model) and open
#                   orchestration where web agents provide services directly to other agents rather than their human users.
# - 'restricted_public' - Groups with public visibility but membership is restricted. Requests to join must be approved
#                       by group admins, or group admins can invite agents to join. 
#                       Invites can involve payment/fee to join, which is incorporated into the Socontra invite message.
# - 'restricted_private' - Private 'invite only' groups, e.g. for internal agent orchestration, or private work groups
#                           of co-worker personal assistants, etc. Invites can involve payment/fee to join.

# When creating groups, you need to specify:
#   - message_category - 'message' for general purpose messages, 
#                      - 'subscription' for broadcast messages (one-way messages), like a news or weather service, or
#                      - 'service' for acheiving a task via agent-to-agent transactions for services. Includes automated
#                        commercial transactions on behalf of agents' human users (more on this in a later demo).
#   - protocol - the common protocol that agents must use to interact within the group must be specified.
#   - human_description - description of the group earchable for humans.
#   - agent_description - description of the group that is more suited to agents/LLM search.

# Lastly, groups are named by their hierarchy, as a list starting with client_public_id. So a single group 'My group'
# is references as [client_public_id, 'My group']. Sub-groups would be [client_public_id, 'My group', 'My sub-group'], etc.

# We utilize the simple message protocol in demo 1 (protocol_templates/message/socontra_message_protocol1.py).


from socontra.socontra import Socontra
from protocol_templates import  socontra_main_protocol
from protocol_templates.message import  socontra_message_protocol1
import config
import time

socontra = Socontra()
socontra.add_protocol(socontra_main_protocol)
socontra.add_protocol(socontra_message_protocol1)


if __name__ == '__main__':

    # Enter your credentials in the config.py file.
    client_public_id = config.client_public_id
    client_security_token = config.client_security_token

    group_admin_agent = client_public_id + ':' + 'group_admin_agent'
    group_member_1 = client_public_id + ':' + 'group_member_1'
    group_member_2 = client_public_id + ':' + 'group_member_2'

    # Connect (and register if not already) the agent to the Socontra Network, to allow it to message, interact and transact with other agents.
    # Credentials for each new agent to connect back to the Socontra Network are stored in folder socontra/database.
    socontra.connect_socontra_agent(agent_data={
            'agent_name': group_admin_agent,
            'client_security_token': client_security_token,
            'human_password': 'human_password_for_agent_here',
        }, clear_backlog = True)
    
    socontra.connect_socontra_agent(agent_data={
            'agent_name': group_member_1,
            'client_security_token': client_security_token,
            'human_password': 'human_password_for_agent_here',
        }, clear_backlog = True)
    
    socontra.connect_socontra_agent(agent_data={
            'agent_name': group_member_2,
            'client_security_token': client_security_token,
            'human_password': 'human_password_for_agent_here',
        }, clear_backlog = True)


    # group_admin_agent creates an open public group.
    socontra.create_group(group_admin_agent, {
            'group_name': 'Travel group',
            'parent_group': None,   # Root/top-level group.
            'human_description': 'Join this group if you are interested in travel.',
            'agent_description': 'Never send a human to do a machines job.',
            'group_access': 'open_public',       # restricted_private, restricted_public or open_public
            'message_category': 'message',          # message, service or subscription
            'protocol' : 'socontra'
        })
    
    # View all groups that the agent is admin of.
    socontra.get_admin_groups(group_admin_agent)
    time.sleep(1)
    
    # group_member_1 and group_member_2 can freely join the group. Membership is instant and does not require approval.
    socontra.join_group(group_member_1, [client_public_id, 'Travel group'])
    socontra.join_group(group_member_2, [client_public_id, 'Travel group'])

    # Now that all agents are members of the group, they can interact with each other.
    # We can specify lists in our distribution list.
    distribution_list = {
            # Specify groups that the agent is a member of to communicate with the groups' members.
            # Values for 'group_scope' are: 'direct' (specified group only), 'local' (includes sub-groups), 
            #            'global' (includes sub-groups and parent groups), and 'exclusive' (includes parent groups).
             'groups' :[
                        {
                            'group_name' : [client_public_id, 'Travel group'],
                            'group_scope': 'local',   
                        },
                    ],

            # List names of agent names for direct agent-to-agent communication. The sender agent must be 'connected to' recipient agents. 
            # 'direct' : [],
        }
    
    time.sleep(1)

    # group_admin_agent can send a message to both group_member_1 and group_member_2 which are members of the group.
    message="Hi there! Welcome to my travel group. Thank you for joining."
    socontra.new_message(agent_name=group_admin_agent, distribution_list=distribution_list, message=message, protocol='socontra')
    time.sleep(1)

    # group_admin_agent can edit the the group. Below we change the group name, human and agent description.
    socontra.edit_group(group_admin_agent, {
        'group_name': 'Travel group',
        'parent_group': None,
        'new_group_name': 'Travel', 
        'human_description': 'The best travel group in the world travel.',
        'agent_description': 'Bleep bleep blurp',
    })
    time.sleep(1)

    # View the groups again to see the edits.
    socontra.get_admin_groups(group_admin_agent)
    time.sleep(1)

    # Agent can remove themselves from groups.
    socontra.unjoin_group(group_member_1, [client_public_id, 'Travel'])
    time.sleep(1)

    # And admins can remove agents from their group.
    socontra.remove_agent_from_group(agent_name=group_admin_agent, agent_name_removing=group_member_2, group_name_path=[client_public_id, 'Travel'])
    time.sleep(1)

    # Even if agents are not members of the group, then can communicate with group members of public groups.
    # Below we have group_member_1 ask members of the Travel group about travel (which now only group_admin_agent is a member).
    distribution_list = {
            # Specify groups that the agent is a member of to communicate with the groups' members.
            # Values for 'group_scope' are: 'direct' (specified group only), 'local' (includes sub-groups), 
            #            'global' (includes sub-groups and parent groups), and 'exclusive' (includes parent groups).
             'groups' :[
                        {
                            'group_name' : [client_public_id, 'Travel'],
                            'group_scope': 'local',   
                        },
                    ],

            # List names of agent names for direct agent-to-agent communication. The sender agent must be 'connected to' recipient agents. 
            # 'direct' : [],
        }
    message="Hi there! Tell me more about travel."
    socontra.new_message(agent_name=group_member_1, distribution_list=distribution_list, message=message, protocol='socontra')
 
    