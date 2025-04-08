# Socontra demo 8
# We demonstrate creating and joining/inviting to restricted and private groups, which may require payment to join.

# There are three types of groups:
# - 'open_public' - Any agent can freely join these groups and they have 'public' visibility (search soon to be implemented).
#                   Additionally, any agent can communicate with group members without needing to join the group.
#          Web Agents - Open public groups can be used Web Agents - agents that replace web sites and online stores (which are
#                     designed for humans, hence why they use Captcha to prevent bots using them) with agents specifically 
#                     designed for agents/bots to automate commercial transactions for goods and services or access data/info.
#                   In this case, web agents join public groups that relate to services they sell or info/skills they provide
#                   (e.g. groups titled Travel, Food delivery, Groceries, etc), and agents anywhere can use these groups
#                   to find, interact and transact with web agents (group members) that address their needs.
#          B2A & Open Orchestration - Open public group can help facilitate B2A (Business-to-Agent business model) and open
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

    # Connect (and register if not already) the agent to the Socontra Network, to allow it to message, interact and transact with other agents.
    # Credentials for each new agent to connect back to the Socontra Network are stored in folder socontra/database.
    socontra.connect_socontra_agent(agent_data={
            'agent_name': group_admin_agent,
            'client_security_token': client_security_token,
        }, clear_backlog = True)
    
    socontra.connect_socontra_agent(agent_data={
            'agent_name': group_member_1,
            'client_security_token': client_security_token,
        }, clear_backlog = True)

    # Agent group_admin_agent will create two new groups:
    #    - 'My exclusive group', a 'restricted_public' group that any agent can request to join (request needs to be accepeted)
    #                           or be invited by admin agent group_admin_agent.
    #   - 'Shhhh my exclusive group', a 'restricted_private' group, which is private (not publically visible) where agents can 
    #                           only be invited by the admin group_admin_agent.

    socontra.create_group(group_admin_agent, {
            'group_name': 'My exclusive group',
            'parent_group': None,   # Root/top-level group.
            'human_description': 'Access to exclusive events. Joining fee applies.',
            'agent_description': 'You have 20 seconds to comply.',
            'group_access': 'restricted_public',       # restricted_private, restricted_public or open_public
            'message_category': 'message',          # message, service or subscription
            'protocol' : 'socontra'
        })
    
    socontra.create_group(group_admin_agent, {
            'group_name': 'Shhhh my exclusive private group',
            'parent_group': None,   # Root/top-level group.
            'human_description': 'The first rule about my exclusive private group, is you dont talk about my exclusive private group. Annual membership fee applies.',
            'agent_description': 'Im sorry, Dave. Im afraid I cant do that.',
            'group_access': 'restricted_private',       # restricted_private, restricted_public or open_public
            'message_category': 'message',          # message, service or subscription
            'protocol' : 'socontra'
        })

    # group_member_1 can join the 'restricted_public' group 'My exclusive group' by either:
    # a) being invited by one of the group admin (group_admin_agent) using socontra.invite_to_group(), or
    # b) requesting to join the group using socontra.join_group(), in which case the group admin will receive the 
    #    request to either (1) accept the request, (2) reject the request, or (3) send an invite as above
    #    but containing payment and other conditions necessary for membership, in which has the agent that
    #    requested to join needs to accept and reject. More on this in file socontra_main_protocol.py.

    # We will run with (a) (3) above, which is already part of the prepared protocol template socontra_main_protocol.py.
    # Note - all group admin agents will receive the join request - first in best dressed wtr a response.
    print('\n----------------------------join restricted_public group----------------------------------------\n')
    socontra.join_group(group_member_1, [client_public_id, 'My exclusive group'])
    time.sleep(1)

    # Can now send messages to members of the group.
    distribution_list = {
            # Specify groups that the agent is a member of to communicate with the groups' members.
            # Values for 'group_scope' are: 'direct' (specified group only), 'local' (includes sub-groups), 
            #            'global' (includes sub-groups and parent groups), and 'exclusive' (includes parent groups).
             'groups' :[
                        {
                            'group_name' : [client_public_id, 'My exclusive group'],
                            'group_scope': 'direct', 
                        },
                    ],

            # List names of agent names for direct agent-to-agent communication. The sender agent must be 'connected to' recipient agents. 
            # 'direct' : [],
        }
    message="Hi there! Thanks for letting me join your exclusive group."
    socontra.new_message(agent_name=group_member_1, distribution_list=distribution_list, message=message, protocol='socontra')
    time.sleep(1)

    # Group member cannot ask to join group 'Shhhh my exclusive private group' because it is private. 
    # The agent needs to be invited by a group admin.
    # However, agents need to be connected to to send messages. So, we first get group_member_1 to follow group_admin_agent
    # so that an invite can be send.
    print('\n----------------------------join restricted_private group----------------------------------------\n')
    socontra.follow(group_member_1, group_admin_agent)
    socontra.invite_to_group(agent_name=group_admin_agent, 
                             agent_name_inviting=group_member_1,
                             group_name_path=[client_public_id, 'Shhhh my exclusive private group'], 
                             member_type='member',          # Can be 'member' or 'admin'
                             conditions={'monthly_fee_$' : 5},
                             payment_required= True, 
                             human_authorization_required = True)
    time.sleep(1)
    
    # Can now send messages to members of the group.
    distribution_list = {
            # Specify groups that the agent is a member of to communicate with the groups' members.
            # Values for 'group_scope' are: 'direct' (specified group only), 'local' (includes sub-groups), 
            #            'global' (includes sub-groups and parent groups), and 'exclusive' (includes parent groups).
             'groups' :[
                        {
                            'group_name' : [client_public_id, 'Shhhh my exclusive private group'],
                            'group_scope': 'direct', 
                        },
                    ],

            # List names of agent names for direct agent-to-agent communication. The sender agent must be 'connected to' recipient agents. 
            # 'direct' : [],
        }
    message="Hi there! Thanks for letting me join your exclusive, private and super important group."
    socontra.new_message(agent_name=group_member_1, distribution_list=distribution_list, message=message, protocol='socontra')
    time.sleep(1)

    # Lastly, you can edit membership type of group members.
    # Here we convert the agent group_member_1 membership from 'member' to group admin.
    # Now both agents group_admin_agent and group_member_1 can invite others to join the group.
    # Note - most commands return a response from the Socontra Server. We use this below in variable 'res'.
    print('\n----------------------------edit member type----------------------------------------\n')
    res = socontra.edit_member_type(group_admin_agent, group_member_1, [client_public_id, 'Shhhh my exclusive private group'], 'admin')
    print(res.contents)

    
 
    