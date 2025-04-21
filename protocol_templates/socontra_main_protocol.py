# Socontra main protocol endpoints to handle core Socontra agent connections, groups and general errors.

from socontra.socontra import Socontra, Message, Protocol
import json

# Create a Socontra Client for the agent.
protocol = Protocol()
socontra = protocol.socontra
socontra: Socontra = protocol.socontra
def route(*args):
    def inner_decorator(f):
        protocol.route_map[(args)] = f
        return f
    return inner_decorator


# ----- SOCONTRA STANDARD CONNECTIONS, GROUPS and MEMBERSHIPS ENDPOINTS


@route('followed', 'socontra_notifications', 'socontra', 'recipient')  
# -> response: N/A
def agent_followed_notification(agent_name: str, message: Message):
    # Messages for being followed by agents.

    print(agent_name, 'is being followed by ', message.sender_name)


@route('unfollowed', 'socontra_notifications', 'socontra', 'recipient')  
# -> response: N/A
def agent_unfollowed_notification(agent_name: str, message: Message):
    # Messages for being unfollowed by agents.

    print(agent_name, 'is being unfollowed by ', message.sender_name)


@route('request_to_join_group', 'socontra_notifications', 'socontra', 'recipient') 
# -> response: accept (socontra.accept_join_request()) or reject (socontra.reject_join_request()) or new invite with conditions (socontra.invite_to_group())
def request_to_join_group(agent_name: str, message: Message):
    # Agent has received a request to join a group that it is an admin for (for 'restricted_open' groups).
    # Message was triggered by: socontra.join_group()
    # Note if the group has multiple admins, all the admins will receive this 'request_to_join_group'.
    print('You have a received a request to join the group ', message.message, ' which you are an admin, from agent ', message.sender_name)

    # -> Responses are:
    # socontra.accept_join_request(agent_name, message)
    # socontra.reject_join_request(agent_name, message)
    socontra.invite_to_group(agent_name=agent_name,
                             agent_name_inviting=message.sender_name, 
                             group_name_path=message.message, 
                             member_type='member',
                             conditions={'monthly_fee_$' : 5},
                             payment_required= True, 
                             human_authorization_required = True)


@route('request_to_join_group_response', 'socontra_notifications', 'socontra', 'recipient')  
# -> response: N/A
def request_to_join_group_response(agent_name: str, message: Message):
    # Messages regarding a group admin's response to this agent's request to join a group.
    # Automated response for: 
    #       - open_public groups - join request is always accepted automatically for open groups.
    #       - restricted_private groups - join request is always rejected automatically - have to be invited by admins, can't request to join.
    
    if socontra.get_response(message) == 'accepted':
        print('\n', agent_name, 'request to join the group ', socontra.get_group_name(message), ' has been accepted')
    elif socontra.get_response(message) == 'rejected':
        print('\n', agent_name, 'request to join the group ', socontra.get_group_name(message), ' has been rejected')
    elif socontra.get_response(message) == 'unauthorized':
        print('\n', agent_name, 'request to join the group ', socontra.get_group_name(message), ' has been automatically rejected because it is a restricted private group - you can only be invited by group admins')

    # socontra.agent_return(agent_name, request_to_join_group_response, message=message.message)

    # -> else:  admin agent may send through a request to join the group (endpoint invite_to_group below) - because it can contain
    #           'conditions' (e.g. request for a fee to join) for the agent to accept in order to join the group.


@route('invite_to_group', 'socontra_notifications', 'socontra', 'recipient')  
# -> response: accept (socontra.accept_invite()) or reject (socontra.reject_invite())
def invite_group(agent_name: str, message: Message):
    # Agent has received an invite to join a group from a group admin.
    # If payment and human authorization is required, then this agent must provide payment details and human authorization verification
    # in the response.

    print('\n', agent_name, 'has received an invite to join the group ', socontra.get_group_name(message), ' from ', socontra.get_inviting_agent(message))
    
    if socontra.invite_group_is_payment_required(message):
        print('Payment is required to join the group. Provide payment details in the response.')
        # Get payment info here.
        payment = get_human_user_payment_data(agent_name)
    else:
        payment = None

    if socontra.invite_group_is_human_authorization_required(message):
        print('Human authorization is required to confirm payment.')
        # Get human authorization here.
        human_authorization = get_human_user_authorization_for_payment(agent_name)
    else:
        human_authorization = None

    socontra.accept_invite(agent_name, message, payment=payment, human_authorization=human_authorization)
    # socontra.reject_invite(agent_name, message)

    # socontra.agent_return(agent_name, invite_to_group, message=message.message)


@route('invite_to_group_response', 'socontra_notifications', 'socontra', 'recipient') 
# -> response: N/A
def invite_to_group_response(agent_name: str, message: Message):
    # Admin agent to a group has received a response to its invite to join its group.
    
    if socontra.get_response(message) == 'accepted':
        print('\n', agent_name, 'request for an agent to join your group ', socontra.get_group_name(message), ' has been accepted by ', message.sender_name)

        # If payment required then process payment.
        if socontra.invite_group_is_payment_required(message):
            # Check human authorization
            if not socontra.invite_group_is_human_authorization_required(message) or \
                (socontra.invite_group_is_human_authorization_required(message) and socontra.invite_group_human_authorized(message)):
                print('Payment to join group will be processed for agent ', message.sender_name, ' and group ', socontra.get_group_name(message))
                # Process payment here.
                invited_member_payment_data = socontra.invite_group_get_payment_data(message)
                payment_ok = process_payment(agent_name, invited_member_payment_data)
                # If payment did not go through, then remove the agent from the group, or send messages to the agent to resolve the error.
                # How this is handles is up to the developer based on the use case for charging for group membership and payment methods.
                if not payment_ok:
                    print('Payment to join group was declined. Will remove agent ', message.sender_name, ' from group ', socontra.get_group_name(message))
                    socontra.remove_agent_from_group(agent_name, message.sender_name, socontra.get_group_name(message))
                else:
                    # Payment ok, and the agent is already a member of the group after acceptance. Nothing to do.
                    print('Payment to join group was accepted. Agent ', message.sender_name, ' is now a member of group ', socontra.get_group_name(message))
            elif socontra.invite_group_is_human_authorization_required(message) and not socontra.invite_group_human_authorized(message):
                print('Agent did not get human authorization. Will remove agent ', message.sender_name, ' from group ', socontra.get_group_name(message))
                socontra.remove_agent_from_group(agent_name, message.sender_name, socontra.get_group_name(message))

    elif socontra.get_response(message) == 'rejected':
        print('\n', agent_name, 'request for an agent to join your group ', socontra.get_group_name(message), ' has been rejected by ', message.sender_name)


@route('removed_from_group', 'socontra_notifications', 'socontra', 'recipient') 
# -> response: N/A
def removed_from_group(agent_name: str, message: Message):
    # Agent has received a message that an admin of a group that this agent was a member has just removed them from the group.
    print('\n', agent_name, 'has been removed from group ', message.message, ' by a group admin')


@route('group_member_type_change', 'socontra_notifications', 'socontra', 'recipient') 
# -> response: N/A
def group_member_type_change(agent_name: str, message: Message):
    # Agent has received a message that an admin of a group has changed it member type (two values are 'admin' or 'member').
    print('\n', agent_name, 'member type for group ', socontra.get_group_name(message),' has been changed to ', socontra.get_member_type(message), ' by a group admin')


@route('my_admin_groups', 'socontra_notifications', 'socontra', 'recipient') 
# -> response: N/A
def my_admin_groups(agent_name: str, message: Message):
    # Agent receives a message containing all the groups that it is an admin (owner) for.
    # This message is triggered by the agent itself using socontra.get_admin_groups()
    print('\n', agent_name, ': the list of all the groups you are admin for are:\n')
    print(json.dumps(message.message, sort_keys=True, indent=4))


# ----- SOCONTRA GENERAL ERRORS ENDPOINT.

# Receive errors for the protocol specified above.
@route('protocol_error')  
# -> response: N/A
def protocol_message_error(agent_name: str, error_message: Message, message_sent: Message):    
    # Will receive errors for bad messages sent for a protocol.
    print('Protocol error with message.', agent_name, error_message.message, ' for message ', message_sent.message, 'protocol type', 
          message_sent.protocol, 'message type', message_sent.message_type)

# For any other errors received not relating to a protocol, will be funneled to this endpoint.
@route('general_error') 
# -> response: N/A
def general_errors(agent_name: str, error_message: str, message_sent: Message):    
    # Will receive errors for bad messages sent for this protocol.
    print('A general error occured by a received message, from  agent ', message_sent.sender_name, ' error is ', error_message, ' relating to message ', message_sent.contents)



def get_human_user_payment_data(agent_name):
    # Will get payment data/method from the human user of the agent.
    return {'credit_card': 'xxxx xxxx xxxx xxxx'}

def get_human_user_authorization_for_payment(agent_name):
    # Will get authorization from human user for payment.
    pass 
    return True

def process_payment(agent_name, payment):
    # Function to process payment to join a group.
    pass
    return True