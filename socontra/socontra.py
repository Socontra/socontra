# This module is the Socontra Client which is the interface between the agent and the Socontra Network. 
# Agents use this Socontra Client to connect to the Socontra network and find, connect, interact and transact to other agents.

from socontra.comms import MessageHTTPResponse, Message, send_auth_message, return_message_object, prepare_agent_api, agent_already_registered, \
                            register_new_agent, recreate_agent_same_credentials, agent_receive_messages, is_agent_already_registered

import queue
import time
import threading
import types

class Protocol:
    def __init__(self, protocol_name: str = None, ignore_missing_endpoints: bool = False):
        self.protocol_name = protocol_name
        self.ignore_missing_endpoints = ignore_missing_endpoints
        self.route_map = {}
        self.socontra = None

class Socontra:
    # Agent base class.
    # Each agent will have an API and predefined process to interact with each other.

    def __init__(self):
        self.agents_connected = {}
        self.route_map = {}
        self.ignore_missing_endpoints = []


    def add_protocol(self, protocol_module):
        # This function is used to add a protocol defined in a separate module.

        # First add all the functions to the Socontra object so that they can be called outside of the module, 
        # as part of the Socontra object, as well as called used by the endpoints in self.route_map.
        for attr, func in protocol_module.__dict__.items():
            if isinstance(func, types.FunctionType) and attr != 'route':
                # Make sure they dont use function names already used in Socontra file.
                if attr in self.__dict__ or attr in Socontra.__dict__:
                    raise ValueError('Two function names are the same. Please rename: ' + str(attr))
                else:
                    setattr(self, attr, func)

        # Add the protocol endpoints so we can call them when messages are received.
        for endpoint, func in protocol_module.protocol.route_map.items():
            # Check if the endpoint is in the route map - can't be repeated. 
            # They can add the 'agent_name' to each endpoint to help make each unique.
            if endpoint not in self.route_map:
                self.route_map[endpoint] = func
            else:
                raise ValueError('Two endpoints are the same. All must be unique. The endpoint is: ', endpoint)

        # If the module requires to ignore missing endpoints, then add it to the list.
        if protocol_module.protocol.ignore_missing_endpoints:
            self.ignore_missing_endpoints.append(protocol_module.protocol.protocol_name)
        
        protocol_module.socontra = self


    # ---------- AGENT CREATION/REGISTRATION CODE - THE AUTH TYPE FUNCTIONS.

    def connect_socontra_agent(self, agent_data, agent_owner_data=None, agent_owner_transaction_config=None, clear_backlog=True):
        # This function will register the agent wanting to connect to the Socontra Network.
        # We will assume that if the agents want to be a supplier, that is a second registration.
        # clear_backlog will clear all the messages that were received whilst the agent was offline/disconnected from the
        # Socontra Network.

        self.agent_name = agent_data['agent_name']
        
        agent_client_id = self.get_client_public_id_name_from_agent_name(agent_data['agent_name'])
        if not agent_client_id:
            raise ValueError('Agent name must contain the public_client_id and colon ":" before the agent name, e.g. "socontra:agent_name"')

        self.agents_connected[agent_data['agent_name']] = { 
                                                            'agent_client_id' : agent_client_id, 
                                                            'queue_return': {},      # To store queues for each agent and endpoint, to pass return values to the main program/agent.
                                                            'protocol_validation' : {}, # To store messages in protocol no longer active for messages, to help control/validate protocols.
        }

        # Set up the queues for each endpoint.
        for k, val in self.route_map.items():
            self.agents_connected[agent_data['agent_name']]['queue_return'][val] = queue.Queue()

        prepare_agent_api(agent_data['agent_name'], self)

        if is_agent_already_registered(agent_data['agent_name'], agent_data['client_security_token']):
            # If new_agent - lets check if the agent credentials already stored in our database (files in folder socontra/database/). 
            response = agent_already_registered(agent_data['agent_name'], agent_data)

            if not response.success:
                # Agent names exists. Will try to recreate the agent - if the agent is an existing registered agent trying to reconnect.
                if 'human_password' in agent_data:
                    response_recreate = recreate_agent_same_credentials(agent_data['agent_name'], agent_data['client_security_token'], agent_data['human_password'])
                    if not response_recreate.success:                
                        # Can't create the agent (i.e conflict or unauthorized) - since an agent with same same name but different credentials exists.
                        raise ValueError('Could not create agent. Agent with the same name exists, no local data about the agent exists, and either: human_password provided does not match with existing agent that is registered; client_security_token is incorrect, or there was an error on the Socontra Network. Please try again.')                        
                    else:
                        response=response_recreate
                else:
                    raise ValueError('Could not create agent. Agent with the same name exists and no local data about the agent exists. If reconnecting the agent, please provide a human_password and client_security_token to authenticate your registered agent.')
        else:
            # Agent not registered. Need to register as a new agent with the Socontra Network.
            response = register_new_agent(agent_data['agent_name'], agent_data, agent_owner_data, agent_owner_transaction_config)

            if response.status_code == 422:
                print('http error response', response.contents)
                raise ValueError('Agent registration fields are not valid. Please check and try again. See print message.')
            elif response.status_code == 401:
                raise ValueError('Client could not be validated. Could not register agent. Re-check your client_public_id and client_security_token, or make sure you are registered with the Socontra Network.')
            elif response.status_code == 500:
                print(f'Error registering agent - Socontra Network error. Response: {response.contents}')
                raise
                
        # Connect the agent to the Socontra Network to receive messages via Server-Sent Events (SSE).
        self.connect_agent_to_socontra_network(agent_data['agent_name'], clear_backlog)

        return response


    # ------------ AGENT CONNECTION MESSAGES
    def join_client_group(self, agent_name: str):
        # Will send a message to the Socontra Network to add this agent to the Client group, meaning that this agent receive
        # all other agents that are also part of the client group (agents part of the developer's account), and vice versa.
        return send_auth_message(agent_name, {}, '/agent_connections/join_client_group', 'PUT')

    def unjoin_client_group(self, agent_name: str):
        # Will send a message to the Socontra Network to remove this agent from the Client group, meaning that this agent can no longer receive
        # messages from other agents that are part of the client group (agents part of the developer's account), and vice versa.
        return send_auth_message(agent_name, {}, '/agent_connections/unjoin_client_group', 'PUT')

    def follow(self, agent_name: str, agent_to_follow: str):
        # Will send a message to the Socontra Network for this agent to follow agent agent_to_follow, meaning that agent_to_follow
        # can communicate with this agent, but not vice versa (this agent can';t comminicate with the other agent unless it follows back) 
        # UNLESS the other agent sends through a task request for services, in which case, this agent can respond in accordance to the 
        # Socontra protocol.
        return send_auth_message(agent_name, {'agent_to_follow_name': agent_to_follow}, '/agent_connections/follow_agent', 'POST')

    def unfollow(self, agent_name: str, agent_to_unfollow: str):
        # Will send a message to the Socontra Network to remove this agent from the Client group, meaning that this agent can no longer receive
        # messages from other agents that are part of the client group (agents part of the developer's account), and vice versa.
        return send_auth_message(agent_name, {'agent_to_unfollow_name': agent_to_unfollow}, '/agent_connections/unfollow_agent', 'DELETE')

    def join_group(self, agent_name: str, group_name_path: list[str]):
        # This command will request the agent to join a group given by group_name, which is the leaf of the group (or root group if parent_group = None),
        # and the list parent_group which specifies the path of the parent groups from the root group to the parent of the next group group_name.
        self.validate_group_name(group_name_path)
        return send_auth_message(agent_name, {'group_name': group_name_path}, '/agent_connections/join_group', 'POST')

    def accept_join_request(self, agent_name: str, message: Message):
        # This function will allow an admin for a group to accept a join request from an agent.
        # The message is just the message received in the join request, making it easy to join.
        
        json_message={
            'agent_name': message.sender_name,
            'group_name': message.message
        }

        return send_auth_message(agent_name, json_message, '/agent_connections/accept_join_group', 'PUT')

    def reject_join_request(self, agent_name: str, message: Message):
        # This function will allow an admin for a group to reject a join request from an agent.
        # The message is just the message received in the join request, making it easy to join.

        json_message={
            'agent_name': message.sender_name,
            'group_name': message.message
        }

        return send_auth_message(agent_name, json_message, '/agent_connections/reject_join_group', 'DELETE')

    def invite_to_group(self, agent_name: str, agent_name_inviting: str, group_name_path: list[str], member_type: str = 'member', 
                        conditions: str | dict = None, payment_required: bool = False, human_authorization_required: bool = False):
        # This function will allow a group's admin to invite an agent to join the group.
        self.validate_group_name(group_name_path)

        json_message = {
            'agent_name': agent_name_inviting,
            'group_name': group_name_path,
            'member_type': member_type,
            'conditions': conditions,
            'payment_required': payment_required,
            'human_authorization_required': human_authorization_required
        }
        
        return send_auth_message(agent_name, json_message, '/agent_connections/invite_group', 'POST')

    def accept_invite(self, agent_name: str, message: Message, payment: dict = None, human_authorization: bool = None):
        # This function will allow an agent to accept an invite (and conditions if any) to join a group sent by an admin of that group.

        json_message = {
            'group_name': message.message['group_name'],
            'agent_name': message.sender_name,
            'inviting_agent': message.message['inviting_agent'],
            'conditions': message.message['conditions'],
            'payment_required': message.message['payment_required'],
            'human_authorization_required': message.message['human_authorization_required'],
            'payment': payment,
            'human_authorization': human_authorization

        }

        return send_auth_message(agent_name, json_message, '/agent_connections/accept_invite_group', 'PUT')
    
    def reject_invite(self, agent_name: str, message: Message):
        # This function will allow an agent to reject an invite (and conditions if any) to join a group sent by an admin of that group.

        json_message = {
            'group_name': message.message['group_name'],
            'agent_name': message.sender_name,
            'inviting_agent': message.message['inviting_agent'],
            'conditions': message.message['conditions'],
            'payment_required': message.message['payment_required'],
            'human_authorization_required': message.message['human_authorization_required'],
        }

        return send_auth_message(agent_name, json_message, '/agent_connections/reject_invite_group', 'DELETE')

    def remove_agent_from_group(self, agent_name: str, agent_name_removing: str, group_name_path: list[str]):
        # Allow admins of a group to remove an agent from the group.
        self.validate_group_name(group_name_path)

        json_message = {
            'group_name': group_name_path,
            'agent_name': agent_name_removing
        }
        
        return send_auth_message(agent_name, json_message, '/agent_connections/remove_agent_from_group', 'DELETE')

    def unjoin_group(self, agent_name: str, group_name_path: list[str]):
        # Will allow an agent to remove themselves from a group.
        self.validate_group_name(group_name_path)
        return send_auth_message(agent_name, {'group_name': group_name_path}, '/agent_connections/unjoin_group', 'DELETE')
    
    def edit_member_type(self, agent_name: str, agent_name_editing: str, group_name_path: list[str], member_type: str):
        # This will allow admin members of a group to change the member type - from 'member' to 'admin' and vice versa.
        self.validate_group_name(group_name_path)
        
        json_message = {
            'agent_name': agent_name_editing,
            'group_name': group_name_path,
            'member_type': member_type
        }

        return send_auth_message(agent_name, json_message, '/agent_connections/edit_member_type', 'PUT')


    # Group creation and editing functions.

    def create_group(self, agent_name: str, group_config: dict):
        # This function will create a new group. Should be in the format:
        '''{
            'group_name': str,
            'parent_group': list[str],      # Optional, None if root/head group.
            'human_description': str,       # Optional
            'agent_description': str,       # Optional
            'group_access': either 'restricted_private', 'restricted_public' or 'open_public',
            'message_category': either 'message', 'service' or 'subscription'
            'protocol': str, any protocol that the developers want to define, or use the default 'socontra' protocols.

        }'''

        # Validate the input. Raise an exception if error.
        self.create_group_validation(group_config)

        # Now that check are complete, send the create group request.
        return send_auth_message(agent_name, group_config, '/agent_groups/create_group', 'POST')

    def edit_group(self, agent_name: str, edit_group_config: dict):
        # This function will edit a group. 
        # For practical and security/privacy reasons of member agents, cannot edit group group_access, message_category or 
        # protocol, e.g. agent may not appreciated being a member of a private group and then that group becoming public.
        # Should be in the format:
        '''{
            'group_name': str,
            'parent_group': list[str],      # Optional, None if root/head group.
            'new_group_name': str,          # Optional, only if changing the group name.
            'human_description': str,         # Optional, only if changing the description.
            'agent_description': str,          # Optional, only if changing the description.
        }'''

        self.edit_group_validation(edit_group_config)
        
        # Now that check are complete, send the create group request.
        return send_auth_message(agent_name, edit_group_config, '/agent_groups/edit_group', 'PUT')

    def get_groups(self, agent_name: str):
        # Will return (via agent message) all the groups that this agent is an admin for or a member of.
        # Will return results in the http response.
        return send_auth_message(agent_name, {}, '/agent_groups/groups', 'GET')
    
    def get_sub_groups(self, agent_name: str, group_name_path: list[str]):
        # Will return the group and sub-groups for group_name_path. Can only perform this command for groups
        # that the agent is member for or are 'restricted_public' or 'open_public'.
        # Will return results in the http response, and only a maximum of 350 subgroups.
        self.validate_group_name(group_name_path)
        json_message = {
            'group_name': group_name_path,
        }
        return send_auth_message(agent_name, json_message, '/agent_groups/subgroups', 'GET')

    def search_groups(self, agent_name: str, client_public_id: str = None, group_name_term: str = None, human_description_term: str = None, agent_description_term: str = None):
        # Will search for non-private groups which contain terms for group_name (group_name_term), human_description 
        # (human_description_term) and agent_description (agent_description_term). Will search if the exact string can be found
        # in the group name or description, and is case insensitive.
        # Will return results in the http response, and only a maximum of 350 groups.

        if not group_name_term and not human_description_term and not agent_description_term:
            raise ValueError('get_groups_search: must specify at least one search term for group_name_term, human_description_term or agent_description_term')
        json_message = {
            'client_public_id': client_public_id,
            'group_name_term': group_name_term,
            'human_description_term': human_description_term,
            'agent_description_term': agent_description_term
        }
        return send_auth_message(agent_name, json_message, '/agent_groups/search_groups', 'GET')

    def add_region_group(self, agent_name: str, group_name_path: list[str], list_of_regions: list[dict[str]]):
        # Will add a list of geographical regions associated with group group_name_path which the agent
        # is (or must be) a member of.
        # If incorrectly specified, Socontra Network will return an error http response. The list_of_regions format is:
        # list_of_regions = [
        #                       {'country': '<country code or name>', 'state': '<state code or name>', 'city': <city name>},
        #                       {...}, ...
        #                   ]
        # <country code or name>, <state code or name> and <city name>  must be the name or ISO codes from country-state-city
        # database from https://github.com/dr5hn/countries-states-cities-database/tree/master (as of May 2025, json file provided 
        # in the socontra/data folder).
        self.validate_group_name(group_name_path)
        self.validate_regions(list_of_regions)
        json_message = {
            'group_name': group_name_path,
            'region_list': list_of_regions
        }
        return send_auth_message(agent_name, json_message, '/agent_groups/add_region_groups', 'POST')
         
    def delete_region_group(self, agent_name: str, group_name_path: list[str], list_of_regions: list[dict[str]]):
        # Will delete a list of geographical regions associated with group group_name_path which the agent
        # is (or must be) a member of.
        # If incorrectly specified, Socontra Network will return an error http response.
        # See function add_region_group() for more information on the format for list_of_regions.
        self.validate_group_name(group_name_path)
        self.validate_regions(list_of_regions)
        json_message = {
            'group_name': group_name_path,
            'region_list': list_of_regions
        }
        return send_auth_message(agent_name, json_message, '/agent_groups/delete_region_groups', 'DELETE')

    def get_region_group(self, agent_name: str, group_name_path: list[str]):
        # Will return all the geographical regions associated with group group_name_path which the agent is a member of.
        # Will return the list in the http response.
        self.validate_group_name(group_name_path)
        json_message = {
            'group_name': group_name_path,
        }
        return send_auth_message(agent_name, json_message, '/agent_groups/get_region_groups', 'GET')


    # ------------ AGENT PROTOCOL MESSAGES

    def new_message(self, agent_name: str, distribution_list: str | dict, message: str | dict, message_type: str='new_message', recipient_type: str='recipient', protocol: str='socontra'):
        # Will send a new message (new dialogue) to one or more agents. This is a general purpose communication/messaging service for agents
        # to communicate what ever they want for their specific use case. The contents of the message is a string or dict/json. 

        if not self.validate_distribution_list(distribution_list):
            raise ValueError('distribution_list error.')
        
        # Create a json message with the message variables to send to the Socontra Network.
        json_message = self.create_json_dict(agent_name=agent_name, distribution_list=distribution_list, message=message, 
                                             message_type=message_type, recipient_type=recipient_type, protocol=protocol)

        # Send the message to the Socontra Network to process.
        http_response = send_auth_message(agent_name, json_message, '/agent_message/message/', 'POST')

        return http_response


    def reply_message(self, agent_name: str, message_reply: str | dict, message_responding_to: Message, message_type: str='message_response', recipient_type: str='recipient'):
        # Agent agent_name will respond to a message received message_responding_to with a message 'message' - BUT only to the sender of the message.
        # Note - can't change protocol - so can't enter that as an input argument - will use what is in the message message_responding_to.

        return self._send_reply(message_responding_to.sender_name, agent_name, message_reply, message_responding_to, message_type, recipient_type)
    

    def reply_all_message(self, agent_name: str, message_reply: str | dict, message_responding_to: str | dict, message_type: str='message_response', recipient_type: str='recipient'):
        # Agent agent_name will respond to a message received message_responding_to with a message 'message' - will reply to all agents in the 
        # distribtion list in message_responding_to.
        # Note - can't change protocol - so can't enter that as an input argument - will use what is in the message message_responding_to.

        return self._send_reply(None, agent_name, message_reply, message_responding_to, message_type, recipient_type)
        

    def _send_reply(self, receiver_name, agent_name, message_reply, message_responding_to, message_type, recipient_type):
        # Agent agent_name will respond to a message received message_responding_to with a message 'message'
    
        # Create a json message with the message variables to send to the Socontra Network.
        json_message = self.create_json_dict(agent_name=agent_name, receiver_name=receiver_name, message_reply=message_reply, 
                                             message_responding_to=message_responding_to.contents, message_type=message_type, 
                                             recipient_type=recipient_type)

        http_response = send_auth_message(agent_name, json_message, '/agent_message/reply_message/', 'POST')

        return http_response
    

    def broadcast(self, agent_name: str, distribution_list: str | dict, message: str | dict, message_type: str='broadcast', recipient_type: str='recipient', protocol: str='socontra'):
        # Will send a broadcast a message to one or more agents. This is a general purpose communication/messaging service for agents
        # to communicate what even they want for their specific use case. The contents of the message can be anything the agents wants. 
        # Socontra just facilitates the communications between agents..

        if not self.validate_distribution_list(distribution_list):
            raise ValueError('distribution_list error.')

        # Create a json message with the message variables to send to the Socontra Network.
        json_message = self.create_json_dict(agent_name=agent_name, distribution_list=distribution_list, message=message, 
                                             message_type=message_type, recipient_type=recipient_type, protocol=protocol)

        http_response = send_auth_message(agent_name, json_message, '/agent_message/broadcast/', 'POST')

        return http_response


    def new_request(self, agent_name: str, distribution_list: str | dict, protocol: str, task: str | dict = None, 
                     message: str | dict = None, proposal: str | dict = None, offer: str | dict = None, recipient_type: str='supplier', 
                     proposal_timeout: int = None, invite_offer_timeout: int = None, offer_timeout: int = None):
        # Will effectively send a task request for services (or products) to one or more agents. 
        # There are four predefined protocols with Socontra. Developers can configure their own protocol. 
        # Hence it is important that the developer selected the right protocol to use.
        # Endpoint message_type = 'new_task_request'

        # Validate the distribution list.
        if not self.validate_distribution_list(distribution_list):
            raise ValueError('distribution_list error.')

        # Ensure one of task, offer or order is specified.
        if task is None and proposal is None and offer is None:
            raise ValueError('You must provide either task, proposal or offer.')

        # Create a json message with the message variables to send to the Socontra Network.
        json_message = self.create_json_dict(agent_name=agent_name, distribution_list=distribution_list, message=message, 
                                             recipient_type=recipient_type, protocol=protocol,
                                             task=task, proposal_timeout=proposal_timeout, proposal=proposal, 
                                             invite_offer_timeout=invite_offer_timeout, offer=offer, offer_timeout=offer_timeout)

        http_response =  send_auth_message(agent_name, json_message, '/agent_message/new_request/', 'POST')

        return http_response


    def request_message(self, agent_name: str, message: str | dict, message_responding_to: Message, recipient_type: str, 
                        message_type: str='request_message'):
        # This is a general purpose message for service/request dialogues/transaction. Can be used to extend or create new service protocols
        # by using the message_type to create new protocol endpoints.
        # Agent agent_name will respond to a service/request message received message_responding_to with a message 'message'.
        
        # Create a json message with the message variables to send to the Socontra Network.
        json_message = self.create_json_dict(agent_name=agent_name, message=message, message_responding_to=message_responding_to.contents,
                                             message_type=message_type, recipient_type=recipient_type)

        http_response =  send_auth_message(agent_name, json_message, '/agent_message/reply_request/', 'POST')

        return http_response


    def submit_proposal(self, agent_name: str, proposal: str | dict, message_responding_to: Message, message: str | dict = None, 
                     recipient_type: str='consumer'):
        # This function will submit a non-binding proposal (on behalf of the supplier) to achieve/fulfill the task.
        # Will only become binding when the consumer sends a 'invite_offer' message (like 'add item to cart'), and this
        # supplier agent responds with an offer, which is binding.
        # Endpoint message_type = 'proposal'
        
        # Create a json message with the message variables to send to the Socontra Network.
        json_message = self.create_json_dict(agent_name=agent_name, message=message, message_responding_to=message_responding_to.contents,
                                             recipient_type=recipient_type, proposal=proposal)

        http_response =  send_auth_message(agent_name, json_message, '/agent_message/submit_proposal/', 'POST')

        return http_response


    def invite_offer(self, agent_name: str, message_responding_to: Message, message: str | dict = None, 
                     recipient_type: str='supplier', invite_offer_timeout: int = None):
        # This function will send an invite_offer message to the supplier asking it to 'formally' submit a binding offer associated
        # with the proposal. This is effectively requesting the supplier to 'add the item to cart'.
        # If the supplier submits the binding offer, then that indicates to the consumer that the item was added to cart.
        # Endpoint messate_type = 'invite_offer'
    
        # Create a json message with the message variables to send to the Socontra Network.
        json_message = self.create_json_dict(agent_name=agent_name, message=message, message_responding_to=message_responding_to.contents,
                                             recipient_type=recipient_type, invite_offer_timeout=invite_offer_timeout)

        http_response =  send_auth_message(agent_name, json_message, '/agent_message/invite_offer/', 'POST')

        return http_response


    def submit_offer(self, agent_name: str, offer: str | dict, message_responding_to: Message, message: str | dict = None, 
                     recipient_type: str='consumer', offer_timeout: int = None, payment_required: bool = False, human_authorization_required: bool = False):
        # This function will 'formally' submit a binding offer (on behalf of the supplier), commiting the supplier (seller) to the offer of services (or products).
        # It will become a mutually binding contract or 'purchase' if the consumer accepts the offer, and which time the offer becomes an 'order' to be executed
        # and delivered by the supplier (agent).
    
        # Create a json message with the message variables to send to the Socontra Network.
        json_message = self.create_json_dict(agent_name=agent_name, message=message, message_responding_to=message_responding_to.contents,
                                             recipient_type=recipient_type,
                                             offer=offer, offer_timeout=offer_timeout, payment_required=payment_required,
                                             human_authorization_required=human_authorization_required)

        http_response = send_auth_message(agent_name, json_message, '/agent_message/submit_offer/', 'POST')

        return http_response


    def reject_invite_offer(self, agent_name: str, message_responding_to: Message, message: str | dict = None, recipient_type: str='consumer'):
        # This function will reject an invite offer, i.e. supplier refuses to send an offer for a previously sent proposal, i.e. supplier won't
        # 'add item to cart', possibly because the item is no longer available. 
        # The invite offer will subsequently be removed from the Socontra Network database.

        # Create a json message with the message variables to send to the Socontra Network.
        json_message = self.create_json_dict(agent_name=agent_name, message=message, message_responding_to=message_responding_to.contents,
                                             recipient_type=recipient_type)

        http_response = send_auth_message(agent_name, json_message, '/agent_message/reject_invite_offer/', 'PUT')

        return http_response


    def reject_task(self, agent_name: str, message_responding_to: Message, message: str | dict = None, recipient_type: str='consumer'):
        # Supplier sends a reject task message to the consumer.
        # This means the supplier officially declines to send a proposal or offer to fulfill the task.

        self.request_message(agent_name, message, message_responding_to, recipient_type, 'reject_task')
    

    def reject_proposal(self, agent_name: str, message_responding_to: Message, message: str | dict = None, recipient_type: str='supplier'):
        # This function will reject a proposal. The proposal, however, will not be removed from the Socontra Network database.
        # This will only send the message, no logic on the Socontra Network needed.

        self.request_message(agent_name, message, message_responding_to, recipient_type, 'reject_proposal')
    

    def accept_offer(self, agent_name: str, message_responding_to: Message, message: str | dict = None, recipient_type: str='supplier',
                     payment: dict=None, human_authorization: bool =None):
        # This function will 'formally' accept an offer, commiting both the consumer (buyer) and supplier (seller) of services (or products).
        # The offer become an 'order' (unless payment info provided, see below), which is a binding agreement between the consumer and supplier.
        # Note that we will allow the code to create an order out of an offer, or proposal, or even a task (for delegation).
        # This function wont check this (that controlled by the developers and how the protocol is configured). We will just enter the order in the message.
        # We will still allow the 'message' to be set - in case developers create their own protocol which can use this.

        # Note that the last two arguments are payment, to provide payment details to the supplier (e.g. credit card) and 
        # human_authorization, which is True or False depnding if the socontra agent did a human verification of the purchase.
        # We have these here for now as placeholders, and will get to these later.
        # ADDITIONALLY - the offer will not become an order until the payment is confirmed by the supplier with payment_confirmed message.

        # Create a json message with the message variables to send to the Socontra Network.
        json_message = self.create_json_dict(agent_name=agent_name, message=message, message_responding_to=message_responding_to.contents,
                                             recipient_type=recipient_type, payment=payment, human_authorization=human_authorization)
        
        http_response = send_auth_message(agent_name, json_message, '/agent_message/accept_offer/', 'POST')

        return http_response


    def payment_confirmed(self, agent_name: str, message_responding_to: Message, message: str | dict = None, recipient_type: str='consumer'):
        # This function will 'formally' create an mutually binding order from an offer after the payment was confirmed, commiting both the 
        # consumer (buyer) and supplier (seller) of services (or products).

        # Create a json message with the message variables to send to the Socontra Network.
        json_message = self.create_json_dict(agent_name=agent_name, message=message, message_responding_to=message_responding_to.contents,
                                             recipient_type=recipient_type)
        
        http_response = send_auth_message(agent_name, json_message, '/agent_message/payment_confirmed/', 'PUT')

        return http_response


    def payment_error(self, agent_name: str, message_responding_to: Message, message: str | dict = None, 
                      recipient_type: str='consumer', offer_timeout: int = None):
        # Notify the consumer agent that there was an error with the payment for the order, e.g. it was denied.
        # The purchase order was therefore not created.
        # offer_timeout is used when this function is used for payment_error, if the agent wants to specify a different timeout.
        # Otherwise, will default to the current offer_timeout.

        # Create a json message with the message variables to send to the Socontra Network.
        json_message = self.create_json_dict(agent_name=agent_name, message=message, message_responding_to=message_responding_to.contents,
                                             message_type='payment_error', recipient_type=recipient_type, offer_timeout=offer_timeout)

        http_response =  send_auth_message(agent_name, json_message, '/agent_message/reply_request/', 'POST')

        return http_response


    def reject_offer(self, agent_name: str, message_responding_to: Message, message: str | dict = None, recipient_type: str='supplier'):
        # This function will 'formally' reject an offer. The offer will subsequently be removed from the Socontra Network database.

        # Create a json message with the message variables to send to the Socontra Network.
        json_message = self.create_json_dict(agent_name=agent_name, message=message, message_responding_to=message_responding_to.contents,
                                             offer=None, message_type='reject_offer', recipient_type=recipient_type)

        http_response = send_auth_message(agent_name, json_message, '/agent_message/reject_offer/', 'PUT')

        return http_response
    
    
    def revoke_offer(self, agent_name: str, offer: str | dict, message_responding_to: Message, message: str | dict = None, recipient_type: str='consumer'):
        # This function will 'formally' revoke an offer. The offer will subsequently be removed from the Socontra Network database.

        # Create a json message with the message variables to send to the Socontra Network.
        json_message = self.create_json_dict(agent_name=agent_name, message=message, message_responding_to=message_responding_to.contents,
                                             offer=offer, message_type='revoke_offer', recipient_type=recipient_type)

        http_response = send_auth_message(agent_name, json_message, '/agent_message/reject_offer/', 'PUT')

        return http_response
       
    def cancel_order(self, agent_name: str, message_responding_to: Message, recipient_type: str, message: str | dict = None):
        # This function will 'formally' cancel an existing and binding (purchase) order. 
        # Unlike offers, since the order is mutually binding and a full contract/agreement, we do not delete it from the Socontra Network 
        # (to keep a paper-trail). We will change its status to canceled.
        # Note - you have to enter a recipient type because both consumer and suppliers can cancel an order.
        
        # For order completion status, these functions are specific so we hardcode the status updates, with certain rules.
        # We have included socontra.update_order_status() for developers to create their own, without any checks.
        message_type = 'cancel_order'

        return self._send_change_order_status(agent_name, message_responding_to, message_type, message, recipient_type)


    def order_complete(self, agent_name: str, message_responding_to: Message, message: str | dict = None, recipient_type: str='consumer'):
        # This function will notify the consumer agent that the order is complete.
        # Unlike offers, since the order is mutually binding and a full contract/agreement, we do not delete it from the Socontra Network 
        # (to keep a paper-trail). We will change its status to order_complete.

        # For order completion status, these functions are specific so we hardcode the status updates, with certain rules.
        # We have included socontra.update_order_status() for developers to create their own, without any checks.
        message_type = 'order_complete'

        return self._send_change_order_status(agent_name, message_responding_to, message_type, message, recipient_type)
    

    def order_failed(self, agent_name: str, message_responding_to: Message, message: str | dict = None, recipient_type: str='consumer'):
        # This function will notify the consumer agent that the order is complete, but failed - was not successful in achieving the task possibly.
        # Unlike offers, since the order is mutually binding and a full contract/agreement, we do not delete it from the Socontra Network 
        # (to keep a paper-trail). We will change its status to order_fail.

        # For order completion status, these functions are specific so we hardcode the status updates, with certain rules.
        # We have included socontra.update_order_status() for developers to create their oww, without any checks.
        message_type = 'order_failed'

        return self._send_change_order_status(agent_name, message_responding_to, message_type, message, recipient_type)


    def order_confirm_success(self, agent_name: str, message_responding_to: Message, message: str | dict = None, recipient_type: str='supplier'):
        # This function will confirm to the supplier agent that the order was complete - like a 'sign-off' on the order which was complete/delivered.
        # This sign-off completes the transaction.
        # Unlike offers, since the order is mutually binding and a full contract/agreement, we do not delete it from the Socontra Network 
        # (to keep a paper-trail). We will change its status to confirm_success.

        # For order completion status, these functions are specific so we hardcode the status updates, with certain rules.
        # We have included socontra.update_order_status() for developers to create their own, without any checks.
        message_type = 'confirm_success'

        return self._send_change_order_status(agent_name, message_responding_to, message_type, message, recipient_type)


    def order_confirm_fail(self, agent_name: str, message_responding_to: Message, message: str | dict = None, recipient_type: str='supplier'):
        # This function will notify to the supplier agent that the completed order was not completed satisfactorily.
        # This is like an agent not providing a 'sign-off' on the order necessary to 'complete' the transaction.
        # Unlike offers, since the order is mutually binding and a full contract/agreement, we do not delete it from the Socontra Network 
        # (to keep a paper-trail). We will change its status to confirm_success.

        # For order completion status, these functions are specific so we hardcode the status updates, with certain rules.
        # We have included socontra.update_order_status() for developers to create their own, without any checks.
        message_type = 'confirm_fail'

        return self._send_change_order_status(agent_name, message_responding_to, message_type, message, recipient_type)


    def change_order_status(self, agent_name: str, message_responding_to: Message, message_type: str, message: str | dict = None, recipient_type: str='consumer'):
        # Use message_type to create unique order status for your own applications. However unlike the standard order status 
        # (order_complete, cancel_order, order_fail, 'confirm_success' 'confirm_fail') which comprises logic on their transition
        # betwene different status types, you will have to manage the logic for any customized order status at the agent client end.

        return self._send_change_order_status(agent_name, message_responding_to, message_type, message, recipient_type)
        

    def _send_change_order_status(self, agent_name: str, message_responding_to: Message, message_type: str, message: str | dict, recipient_type: str):
        # Will execute the messages for changing the order status for messages: order_complete, cancel_order, order_fail, 'confirm_success' 'confirm_fail'.
        # Use message_type to create unique order status for your own applications (via the change_order_status() function), 
        # however you will have to manage the logic at the agent client end.

        # Create a json message with the message variables to send to the Socontra Network.
        json_message = self.create_json_dict(agent_name=agent_name, message=message, message_responding_to=message_responding_to.contents,
                                             message_type=message_type, recipient_type=recipient_type)
        
        http_response = send_auth_message(agent_name, json_message, '/agent_message/order_complete_or_cancel_status/', 'PUT')

        return http_response


    def task_withdrawn(self, agent_name: str, message_responding_to: Message, message: str | dict = None, recipient_type: str='supplier'):
        # Consumer sends a task withdrawn message to the supplier.
        # Note that Socontra Network will do this automatically when the dialogue/transaction to fulfill the task has been closed.
        # But there are scenarios where the task/dialogue/transaction is still open (e.g. waiting for order to be fulfilled) and the
        # agent want to send an agent a task withdrawn to close the transcation for them specifically.

        self.request_message(agent_name, message, message_responding_to, recipient_type, 'task_withdrawn')


    def send_protocol_error(self, agent_name: str, received_message: Message, error_message: str | dict):
        # Will send the agent in received_message a protocol error_message.

        # Can use reply message.
        self.reply_message(agent_name, error_message, received_message, 'protocol_error', 'recipient')


    # ----Protocol validation and control

    def close_dialogue(self, agent_name: str, message_responding_to: Message):
        # Will close the dialogue/transaction. 
        # If closed by the dialogue initiator, no more messages or responses can be sent or received by any agent for this
        # dialogue after it is closed.
        # If closed by other agents in the dialogue, no more messages can be received by this agent after the dialogue has been closed.

        # Create a json message with the message variables to send to the Socontra Network.
        json_message = self.create_json_dict(agent_name=agent_name, message_responding_to=message_responding_to.contents,
                                             close_dialogue_id=True)

        return send_auth_message(agent_name, json_message, '/agent_message/close_protocol_control/', 'POST')
    

    def close_agent(self, agent_name: str, message_responding_to: Message):
        # Will close the dialogue/transaction with the agent in the message message_responding_to. No more messages can be received from 
        # this agent after this agent has been closed.

        # Create a json message with the message variables to send to the Socontra Network.
        json_message = self.create_json_dict(agent_name=agent_name, message_responding_to=message_responding_to.contents,
                                             close_agent_name=message_responding_to.sender_name)

        return send_auth_message(agent_name, json_message, '/agent_message/close_protocol_control/', 'POST')


    def close_message(self, agent_name: str, close_message_type: str | list[str], message_responding_to: Message):
        # Will close the message_type(s) in the dialogue/transaction. No more messages can be received from
        # any agent that sends a message of type close_message_type after it is closed.
        # close_message_type can be a string with one message_type, or a list of multiple message types to close.

        if type(close_message_type) == str:
            close_message_type = [close_message_type]

        # Create a json message with the message variables to send to the Socontra Network.
        json_message = self.create_json_dict(agent_name=agent_name, message_responding_to=message_responding_to.contents,
                                             close_message_type=close_message_type)

        return send_auth_message(agent_name, json_message, '/agent_message/close_protocol_control/', 'POST')


    def close_all_dialogues(self, agent_name):
        # This function will deactivate all active protocol dialogues that the agent had going.

        return send_auth_message(agent_name, {}, '/agent_message/deactivate_all_dialogues/', 'PUT')


    def protocol_validation(self, agent_name, received_message: Message, message_responding_to: Message = None, valid_message_types: str | list = None):
        # This function will check if the message_type for current message is consistent with what is allowed for the message_responding_to.
        # This is done by checking if message_responding_to are listed in the input argument valid_message_types. 
        # Always let 'task_withdrawn" through at any stage.

        # Future version will move this protocol flow validation to the Socontra Network, allowing developers to configure and 
        # share protocols and templates, and ensure all users of the protocol abide by the same protocol flow/rules.

        if received_message.message_type == 'task_withdrawn':
            return True
        elif type(valid_message_types) == str and message_responding_to.message_type != valid_message_types:
            self.send_protocol_error(agent_name, received_message, error_message=f'Message type {received_message.message_type} is not a valid response to message_responding_to of message type {message_responding_to.message_type}.')
            return False
        elif type(valid_message_types) == list:
            for message_type_to_validate in valid_message_types:
                if message_responding_to.message_type == message_type_to_validate:
                    return True
            self.send_protocol_error(agent_name, received_message, error_message=f'Message type {received_message.message_type} is not a valid response to message_responding_to of message type {message_responding_to.message_type}.')
            return False
        else:
            # valid_message_types = None, i.e. no prior message types needed for validation. Return True. 
            return True

    # ----Route messages to endpoints
    
    def route_message(self, agent_name, message, message_category, message_type = None):
       # Will route the message to the correct endpoint.

        # Get the message type from the message, if not message type overide given by message_type argument.
        if message_type == None:
            message_type = message['message_type']

        recipient_type = message['recipient_type']

        # Get the protocol.
        protocol = message['protocol']

        # See if there is a previous message to the message, e.g. if it is a response to a message.
        if 'message_responding_to' in message or 'message_sent' in message:
            message_responding_to = self.get_message_responding_to(message)
            self.delete_message_responding_to(message)
        else:
            message_responding_to = None

        # Similarly, if there is payment and human_authorization info in the message, take it out and pass it separately.
        if 'payment' in message:
            payment = message['payment']
            human_authorization = message['human_authorization']
            del message['payment']
            del message['human_authorization']
        else:
            payment, human_authorization = None, None
        
        # Convert message and message_responding_to to objects to make it nicer for the developer to access the data.
        message_obj = return_message_object(message, message_type)

        # print('Message to be routed is', agent_name, message_type, message_category, protocol, recipient_type)

        # Create the endpoint tuple based on whether there is an agent_specific endpoint, or just general endpoints for the message.
        
        if (agent_name, message_type, message_category, protocol, recipient_type) in self.route_map:
            endpoint_tuple = (agent_name, message_type, message_category, protocol, recipient_type)
        elif (message_type, message_category, protocol, recipient_type) in self.route_map:
            endpoint_tuple = (message_type, message_category, protocol, recipient_type) 
        elif message_type == 'protocol_error':
            if (agent_name, 'protocol_error') in self.route_map:
                endpoint_tuple = (agent_name, 'protocol_error')
            elif ('protocol_error',) in self.route_map:
                endpoint_tuple = ('protocol_error',)
            else:
                return
            message_responding_to_obj = return_message_object(message_responding_to)
            self.route_map[endpoint_tuple](agent_name, message_obj, message_responding_to_obj)
            return
        elif protocol in self.ignore_missing_endpoints:
            # If want to ignore messages that dont have endpoints, do nothing, just return.
            return
        else:
            # If it gets here, there is no endpoint for the protocol message. Therefore send a 'general error'
            # if an endpoint exists. If not, do nothing and ignore the message.
            if (agent_name, 'general_error') in self.route_map:
                endpoint_tuple = (agent_name, 'general_error')
            elif ('general_error',) in self.route_map:
                endpoint_tuple = ('general_error',)
            else:
                return
            error_message = 'Message received with no endpoint to route it.'
            self.route_map[endpoint_tuple](agent_name, error_message, message_obj)
            return

        try:
            if not message_responding_to:
                self.route_map[endpoint_tuple](agent_name, message_obj)
            elif not payment:
                message_responding_to_obj = return_message_object(message_responding_to)
                self.route_map[endpoint_tuple](agent_name, message_obj, message_responding_to_obj)
            else:
                # Must be payment info for a supplier. Pass the variables.
                message_responding_to_obj = return_message_object(message_responding_to)
                self.route_map[endpoint_tuple](agent_name, message_obj, message_responding_to_obj, payment, human_authorization)
        except:
            print('Message to be routed that caused the error:', agent_name, message_type, message_category, protocol, recipient_type)
            raise ValueError('Message endpoint could not be found.')


    def agent_return(self, agent_name, function_at_endpoint, **kwargs):
        # Will add the variables *kwargs to a dict and place it on a queue, for the agent to  retract it later.
        
        # Create a dict with the return values in *kwargs
        return_dict_to_queue = {}
        for k, val in kwargs.items():
            return_dict_to_queue[k] = val

        # Store on the queue.
        self.agents_connected[agent_name]['queue_return'][function_at_endpoint].put(return_dict_to_queue)


    def expect(self, agent_name, function_at_endpoint, timeout = None):
        # Will check the queue and remove an item - which is/are return values from an endpoint.
        
        if timeout is None:
            item_on_queue = self.agents_connected[agent_name]['queue_return'][function_at_endpoint].get()
        elif timeout==0:
            try:
                item_on_queue = self.agents_connected[agent_name]['queue_return'][function_at_endpoint].get_nowait()
            except queue.Empty:
                return None
        else:
            try:
                item_on_queue = self.agents_connected[agent_name]['queue_return'][function_at_endpoint].get(timeout=timeout)
            except queue.Empty:
                return None
        self.agents_connected[agent_name]['queue_return'][function_at_endpoint].task_done()

        return item_on_queue
    

    def expect_multiple(self, agent_name, list_of_functions_at_endpoint, timeout = None):
        # Will do the same as expect() above except will monitor multiple endpoints listed in the list list_of_functions_at_endpoint,
        # and will return when the first endpoint receives a message and a return value is passed to this agent.

        # Will return the name of the endpoint function that received the message, and the value that was passed to the agent
        # using the function socontra.agent_return().

        self.expect_multiple_return_value = None
        self.expect_multiple_return_function_name = None

        # Will run this in a thread just in case holds up anything in other code.
        expect_multiple_thread = threading.Thread(target=self._expect_multiple_thread, args=(agent_name, list_of_functions_at_endpoint, timeout))

        expect_multiple_thread.start()
        expect_multiple_thread.join()

        return self.expect_multiple_return_function_name, self.expect_multiple_return_value


    def _expect_multiple_thread(self, agent_name, list_of_functions_at_endpoint, timeout):
        # Will loop and check all queues in list_of_functions_at_endpoint until an item is found/get from one of the threads
        # associated with list_of_functions_at_endpoint.

        run_at_least_once = True
        if timeout is not None:
            time_end = time.time() + timeout
            run_until_completion = False
        else:
            run_until_completion = True
        while run_at_least_once or run_until_completion or time.time() < time_end:
            for each_endpoint_queue_func in list_of_functions_at_endpoint:
                return_value = self.expect(agent_name, each_endpoint_queue_func, 0)
                if return_value is not None:
                    self.expect_multiple_return_value = return_value
                    self.expect_multiple_return_function_name = each_endpoint_queue_func.__name__
                    return
            time.sleep(0.1)     # Not sure if this is too low, using CPU unnecessarily, but will have to do for now.
            run_at_least_once = False
        # Did not receive a message in the time. Return None for both return values.
        self.expect_multiple_return_value = None
        self.expect_multiple_return_function_name = None
        return


    # General Socontra functions

    def connect_agent_to_socontra_network(self, agent_name, clear_backlog):
        # Start the API (Sever Sent Events) API to receive messages from the Socontra Network.
        agent_connected = {}
        agent_connected['agent_connected'] = False
        agent_api_service = threading.Thread(target=agent_receive_messages, args=(agent_name, clear_backlog, agent_connected))
        agent_api_service.start()

        # Wait until it has authenticated and connected to the network before continuing, so the main code does not start 
        # before the agent is connected and fully authenticated with the Socontra Network.
        while not agent_connected['agent_connected']:
            time.sleep(0.1)

    def get_client_public_id_name_from_agent_name(self, agent_name):
        # Get the agent_client_id, i.e. the client_public_id, from agent_name, which is the text before the ':' 
        # since agent_name = 'client_public_id:name_of_agent'.
        agent_name_copy = agent_name
        try:
            return agent_name_copy[:agent_name_copy.index(':')]
        except:
            return False
    
    def get_deadline(self, timeout_as_epoch_time):
        return time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(timeout_as_epoch_time))
    
    def timeout_not_expired(self, timeout):
        # Will return True if timeout not expired.
        return time.time() < timeout

    def invite_group_is_payment_required(self, message: Message):
        # Will return true if the message says that payment is required.
        return message.message['payment_required']
    
    def invite_group_is_human_authorization_required(self, message: Message):
        # Will return true if the message says that human authorization is required.
        return message.message['human_authorization_required']
    
    def invite_group_human_authorized(self, message: Message):
        # Will return true if human authorization in the message is true.
        return message.message['human_authorization']
    
    def invite_group_get_payment_data(self, message: Message):
        # Will return true if human authorization in the message is true.
        return message.message['payment']
    
    def get_response(self, message: Message):
        # Will return the response to a request_to_join_group_response message.
        return message.message['response']
    
    def get_group_name(self, message: Message):
        # Will return the group name in a message.
        return message.message['group_name']
    
    def get_inviting_agent(self, message: Message):
        # Will return the inviting agent in a message.
        return message.message['inviting_agent']
    
    def get_member_type(self, message: Message):
    # Will return the member type in a message.
        return message.message['member_type']


    def validate_distribution_list(self, distribution_list):
        # Will validate the distribution list and return True if ok and False otherwise.
        # Region names must be consistent with data/countries+states+cities.json from https://github.com/dr5hn/countries-states-cities-database.

        # distribution_list = {
        #   'groups' : [
        #            {
        #                'group_name' : ['socontra_demo', 'A restricted public group'],
        #                'group_scope': 'local',  # Values are 'direct' (specified group only), 'local' (group and sub-groups), 'global' (all group, sub-groups and parent groups), and 'exclusive' (group and parent groups). Default = 'local'.
        #                'regions'  : {'country' : 'Australia', 'state' : 'Victoria', 'city': 'Melbourne'}, # can have country only, or country + state only, or all three country + state + city.
        #                'region_scope': 'local',    # as above
        #            },
        #           {...}, {...}, ...
        #         ],
        #     ],
        #   'regions': [
        #               {'country': <country>, 'state': <state>, 'city': city}
        #       ],
        #   'direct' : ['socontra_demo:supplier_agent_1'],
        #   }        

        if type(distribution_list) == str:
            return True
        elif type(distribution_list) != dict:
            return False
        
        # If here, the distribution list is a dict. Check the components are there as required.
        # Check if contains either direct or group distribution list.
        if 'groups' not in distribution_list and 'direct' not in distribution_list:
            return False
        # Direct must be a list.
        if 'direct' in distribution_list and type(distribution_list['direct']) != list:
            return False
        
        # Groups must be a list
        if 'groups' in distribution_list and type(distribution_list['groups']) != list:
            return False
        elif 'groups' in distribution_list:
            # Go through each element in the list and make sure contains the correct elements.
            for group_distribution in distribution_list['groups']:
                # Need both group name and group scope.
                if 'group_name' not in group_distribution or 'group_scope' not in group_distribution:
                    return False
                if type(group_distribution['group_name']) != list:
                    return False
                if not (group_distribution['group_scope'] == 'local' or group_distribution['group_scope'] == 'direct' or \
                        group_distribution['group_scope'] == 'global' or group_distribution['group_scope'] == 'exclusive'):
                    return False
        
        # If regions are specified, regions must be a list.
        if 'regions' in distribution_list and type(distribution_list['regions']) != list:
            return False
        elif 'regions' in distribution_list:
            # Go through each element in the list and make sure contains the correct elements.
            # Actual names of country, state and city will be chgecked on the Socontra Network.
            for a_region in distribution_list['regions']:
                # Need at least country.
                if 'country' not in a_region:
                    return False
                # If specifiy city, must have state specified.
                if 'city' in a_region and 'state' not in a_region:
                    return False
        
        return True
        
    def validate_regions(self, list_of_regions):
        # Will validate the regions list. Should be in format:
        #   [
        #       {'country': <country>, 'state': <state>, 'city': city},
        #       {...}
        #   ],

        # list_of_regions should be a list.
        if  type(list_of_regions) != list:
            raise ValueError('list_of_regions must be a list.')

        # Go through each element in the list and make sure contains the correct elements.
        # Actual names of country, state and city will be chgecked on the Socontra Network.
        for a_region in list_of_regions:
            # Need at least country.
            if 'country' not in a_region:
                 raise ValueError('Each region in list_of_regions must specify a country.')
            # If specifiy city, must have state specified.
            if 'city' in a_region and 'state' not in a_region:
                raise ValueError('Each region in list_of_regions must specify a state if the city is specified.')
        
        return True

    def create_group_validation(self, group_config):
        # Will validate create group configuration.
        '''socontra.create_group({
            'group_name': 'My first group',
            'parent_group': ['socontra_demo', 'Lets edit all the sub-groups'],
            'human_description': 'This group is amazing.',
            'agent_description': 'Bleep bleep blurp',
            'group_access': 'restricted_private',
            'message_category': 'message',
            'protocol' : 'socontra'
        })'''

        '''{
            'group_name': str,
            'parent_group': list[str],      # Optional, None if root/head group.
            'human_description': str,       # Optional
            'agent_description': str,       # Optional
            'group_access': either 'restricted_private', 'restricted_public' or 'open_public',
            'message_category': either 'message', 'service' or 'subscription'
            'protocol': str, any protocol that the developers want to define, or use the default 'socontra' protocols.

        }'''

        # Might as well do a check here and raise an error.
        if not group_config or type(group_config) != dict:
            raise ValueError('No create group data provided or was not a dict.')
                
        if 'group_name' not in group_config or 'group_access' not in group_config or 'message_category' not in group_config or 'protocol' not in group_config:
            raise ValueError('Create group data must contain group_name, group_access, message_category and protocol.')
        
        if type(group_config['group_name']) != str or type(group_config['protocol']) != str:
             raise ValueError('group_name and protocol must be a string.')
        
        if not (group_config['group_access'] == 'restricted_private' or 
                group_config['group_access'] == 'restricted_public' or
                group_config['group_access'] == 'open_public'):
            raise ValueError('Create group group_access must be one of values: restricted_private, restricted_public or open_public.')

        if not (group_config['message_category'] == 'message' or 
                group_config['message_category'] == 'service' or
                group_config['message_category'] == 'subscription'):
            raise ValueError('Create group message_category must be one of values: message, service or subscription.')
        
        self._validate_parent_group_human_agent_descr(group_config)

        # Lastly check that the chars '~>' are not in the agent name.
        if '~>' in group_config['group_name']:
            raise ValueError('group_name cannot contain "~>".')
        

    def edit_group_validation(self, edit_group_config):
        # Validate the following format:
        '''{
            'group_name': str,
            'parent_group': list[str],      # Optional, None if root/head group.
            'new_group_name': str,          # Optional, only if changing the group name.
            'human_description': str,         # Optional, only if changing the description.
            'agent_description': str,          # Optional, only if changing the description.
        }'''

        if not edit_group_config or type(edit_group_config) != dict:
            raise ValueError('No create group data provided or it was not a dict.')
        
        if 'group_name' not in edit_group_config or type(edit_group_config['group_name']) != str:
            raise ValueError('group_name to edit not provided or is not a string.')
        
        if 'new_group_name' not in edit_group_config and 'human_description' not in edit_group_config and 'agent_description' not in edit_group_config:
            raise ValueError('Edit group data must contain at least one of new_group_name, human_description or agent_description.')
        
        if 'new_group_name' in edit_group_config:
            if type(edit_group_config['new_group_name']) != str:
                raise ValueError('new_group_name must be a string.')
            
            # Check that the chars '~>' are not in the agent name.
            if '~>' in edit_group_config['new_group_name']:
                raise ValueError('new_group_name cannot contain "~>".')
        
        self._validate_parent_group_human_agent_descr(edit_group_config)
        

    def _validate_parent_group_human_agent_descr(self, group_config):
        # Will validate group_name, human_description and agent_description as optional conponents in a create_group
        # or edit_group function.
        # parent_group can be None if it is the root/top-level group.

        if 'parent_group' in group_config and group_config['parent_group'] is None:
            pass
        elif 'parent_group' in group_config and type(group_config['parent_group']) != list:
            raise ValueError('parent_group must be a list of strings.')
        elif 'parent_group' in group_config and any(type(name) != str for name in group_config['parent_group']):
            raise ValueError('an element in parent_group is not a string.')
        
        if 'human_description' in group_config and type(group_config['human_description']) != str:
            raise ValueError('human_description must be a string.')
        
        if 'agent_description' in group_config and type(group_config['agent_description']) != str:
            raise ValueError('agent_description must be a string.')
        

    def validate_group_name(self, group_name_path):
    # We can create the full group name here and not in the API like groups.
        if not(type(group_name_path) == list and group_name_path and not any(type(name) != str for name in group_name_path)):
            raise ValueError('group_name_path should be a list of strings.')

    def create_json_dict(self, **kwargs):
        # Will create a json dict from the arguments entered.
        json_message = {}
        for k, val in kwargs.items():
            json_message[k] = val

        return json_message
        
    def get_message_responding_to(self, message):
        # Will return the message_responding_to in the message, used to indicate what the next step of the protocol is in response to.
        # Get the message that the agent is responding to.
        if 'message_responding_to' in message:
            return message['message_responding_to']
        
        # now check if there is a underlying message when receiving a protocol_error response form the Socontra Network
        elif 'message_sent' in message:
            return message['message_sent']
        
        # Otherwise return None.
        else:
            return None
        
    def delete_message_responding_to(self, message):
        # Will delete the message_responding_to in the message, as we return it separately from the message received to the endpoint.
        if 'message_responding_to' in message:
            del message['message_responding_to']
        
        # now check if there is a underlying message when receiving a protocol_error response form the Socontra Network - delete that.
        elif 'message_sent' in message:
            del message['message_sent']