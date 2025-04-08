# Socontra template for the 'transact' protocol, suitable for automated agent-to-agent commercial transactions.
# Protocol for the consumer of services.

import time

from bisect import insort

from socontra.socontra import Socontra, Message, Protocol

# Create a Socontra Client for the agent.
protocol = Protocol()
socontra:Socontra = protocol.socontra
def route(*args):
    def inner_decorator(f):
        protocol.route_map[(args)] = f
        return f
    return inner_decorator


# ----- SOCONTRA PROTOCOL: 'transact' - allocation of a task to agents  -------------------------------------


@route('proposal', 'service', 'transact', 'consumer')  
# -> response: socontra.invite_offer(), or to end dialogue with the supplier either: socontra.reject_proposal(), socontra.task_withdrawn(), or NoComms
def receive_proposal(agent_name: str, received_message: Message, message_responding_to: Message):
    # The Socontra standard allocate protocol.
    # Consumer agent
    # The supplier has submitted a non-binding proposal to fulfill the consumer's task.
    # This is equilavent to returning product search results in online stores.

    # Protocol validation. Messages are only valid if the previous message in the dialogue (message_responding_to) was 'new_task_request'.
    if not socontra.protocol_validation(agent_name, received_message, message_responding_to, valid_message_types=['new_task_request']):
        return
    
    print(f'\nProposal to fulfill the task was submitted by  {received_message.sender_name}. The proposal is {received_message.proposal}\n')

    # In our example, we return the proposals to the main consumer orchestrator to evaluate this and other proposals that are received.
    socontra.agent_return(agent_name, receive_proposal, received_message=received_message)


@route('reject_task', 'service', 'transact', 'consumer')  
# -> response: end dialogue with the supplier.
def reject_task_consumer(agent_name: str, received_message: Message, message_responding_to: Message):    
    # The Socontra standard transact protocol.
    # Consumer agent
    # Supplier sends a reject task request message to the consumer, formally declining to send a proposal to the consumer.
    # Possibly no suitable proposals to achieve the task request.

    # Protocol validation. Messages are only valid if the previous message in the dialogue (message_responding_to) was 'new_task_request'.
    if not socontra.protocol_validation(agent_name, received_message, message_responding_to, valid_message_types=['new_task_request']):
        return
    
    print('\nSupplier rejected to submit an offer to fulfill task ', received_message.task, '. The supplier is ', received_message.sender_name, '. The reason/message is ', received_message.message, '\n')

    # In our example, we just ignore reject_task messages. We do not return this message to the orchestrator (unnecessary).


@route('offer', 'service', 'transact', 'consumer')  
# -> response: socontra.accept_offer(), or end the dialogue with this supplier with: socontra.reject_offer(), 
#              socontra.task_withdrawn(), NoComms (offer will timeout by received_message.offer_timeout)
def receive_offer(agent_name: str, received_message: Message, message_responding_to: Message):
    # The Socontra standard transact protocol.
    # Consumer agent
    # The supplier has submitted a committed and binding 'offer' to fulfill the consumer's task.
    # This is equilavent to being informed that 'item is added to cart' for online stores, ready for purchase.
    # If the consumer accepts the offer (optionally with payment), it becomes a mutually binding contract or 
    # 'purchase' for the services or product. In this case, the offer becomes an (purchase) 'order', to be 
    # executed and delivered by the supplier (agent).

    # Protocol validation.
    if not socontra.protocol_validation(agent_name, received_message, message_responding_to, valid_message_types=['invite_offer']):
        return
        
    print('\nOffer to fulfill the task was submitted by  ', received_message.sender_name, '. The offer is ', received_message.offer, 
          ' A response is required by', socontra.get_deadline(received_message.offer_timeout), '\n')

    # In this example, we return the response to the main consumer orchestrator to manage,
    # because if the offer is not accepted by the consumer, via either socontra.reject_offer(), socontra.task_withdrawn()
    # or NoComms, or the supplier sends a socontra.revoke_offer(), then the consumer agent needs to go back to 
    # the 'proposal' stage to select another proposal option ('invite_offer') to achieve the task.
    socontra.agent_return(agent_name, receive_offer, received_message=received_message)
    

@route('reject_invite_offer', 'service', 'transact', 'consumer') 
# -> response: Go back to 'proposal' stage to select another proposal.
def reject_invite_offer_consumer(agent_name: str, received_message: Message, message_responding_to: Message):
    # The Socontra standard transact protocol.
    # Consumer agent
    # The supplier has refused to submit an offer (did not add item to cart) for a proposal it previously submitted.
    # Could be that it is no longer available, which could be the case when transacting in dynamic domains.

    # Protocol validation.
    if not socontra.protocol_validation(agent_name, received_message, message_responding_to, valid_message_types=['invite_offer']):
        return
    
    print('\nInvite offer for a proposal was rejected by  ', received_message.sender_name, '. The proposal was ', received_message.proposal, '\n')

    # Return the value so that the main consumer orchestrator can respond appropriately (select an alternative proposal).
    socontra.agent_return(agent_name, reject_invite_offer_consumer, received_message=received_message)


@route('payment_confirmed', 'service', 'transact', 'consumer')  
# -> response: wait for completion/delivery message from supplier, or
#              socontra.request_message() (provide info needed to execute the order) or socontra.cancel_order().
def payment_confirmed_consumer(agent_name: str, received_message: Message, message_responding_to: Message):
    # The Socontra standard transact protocol.
    # Consumer agent
    # The supplier has confirmed that payment for an order has been successful. The order is established and binding, and the
    # supplier should be executing it to completion/delivery (unless canceled prior).

    # Protocol validation.
    if not socontra.protocol_validation(agent_name, received_message, message_responding_to, valid_message_types=['accept_offer']):
        return
    
    # To support protocol control/logic, we can 'close messages' which are no longer valid as we progress through the protocol.
    # We can also socontra.close_agents() if we want to stop a dialogue with a specific agent.
    socontra.close_message(agent_name, close_message_type=['offer', 'reject_invite_offer', 'revoke_offer', 'proposal', 'reject_task'], message_responding_to=received_message)
    
    print('\nPayment for order successful. Order to fulfill task in progress by ', received_message.sender_name, '. The (purchase) order is ', received_message.order, '\n')
     
     # Return the message back to the consumer orchestrator to track and manage the order completion and delivery.
    socontra.agent_return(agent_name, payment_confirmed_consumer, received_message=received_message)


@route('payment_error', 'service', 'transact', 'consumer')  
# -> response: go back to 'offer' stage and resend the socontra.accept_offer() with updated payment details, 
#              or go back to 'proposal' stage and select another proposal from another supplier with socontra.invite_offer().
def payment_error_consumer(agent_name: str, received_message: Message, message_responding_to: Message):
    # The Socontra standard transact protocol.
    # Consumer agent
    # Payment for the order has been declined. Could be because of a payment error (e.g. credit card declined or incorrect) or 
    # error with the human_authorization for the purchase. Purchase order was not created. 
    # Consumer can try again or look to select another proposal by another supplier.

    # Protocol validation.
    if not socontra.protocol_validation(agent_name, received_message, message_responding_to, valid_message_types=['accept_offer']):
        return
    
    print('\nPayment for order unsuccessful from ', received_message.sender_name, ' because of ', received_message.message,'. Purchase order failed, which was ', 
          received_message.offer, ' requires a resolution response by ', socontra.get_deadline(received_message.proposal_timeout), '\n')
     
    socontra.agent_return(agent_name, payment_error_consumer, received_message=received_message)


@route('revoke_offer', 'service', 'transact', 'consumer')
# -> response: Go back to 'proposal' stage and socontra.invite_offer() another proposal.
def revoke_offer_consumer(agent_name: str, received_message: Message, message_responding_to: Message):
    # The Socontra standard transact protocol.
    # Consumer agent
    # The supplier has revoked an offer it submitted BEFORE the consumer agent could accept it and form a mutually binding 
    # agreement (purchase). This is consistent with contract law.

    # Protocol validation.
    if not socontra.protocol_validation(agent_name, received_message, message_responding_to, valid_message_types=['invite_offer']):
        return
    
    # Agent response
    print('\nOffer has been revoked by the supplier ', received_message.sender_name, '. The offer was ', received_message.proposal, '\n')

    # Return the value so that the main consumer orchestrator can replan and select an alternative proposal.
    socontra.agent_return(agent_name, revoke_offer_consumer, received_message=received_message)


@route('request_message', 'service', 'transact', 'consumer') 
# -> response: NoComms (wait for order complete message), socontra.request_message() (reply to message) or socontra.cancel_order()
def request_message_consumer(agent_name: str, received_message: Message, message_responding_to: Message):
    # The Socontra standard transact protocol.
    # Consumer agent
    # Supplier sent a message to the consumer.
    # These messages can be used for sending messages between consumer and supplier necessary to complete the order in order to fulfill/achieve the task.

    # Protocol validation.
    if not socontra.protocol_validation(agent_name, received_message, message_responding_to, valid_message_types=['accept_offer', 'request_message']):
        return

    print('\n', received_message.sender_name, ' sent a message relating to the order, which is ', received_message.message, '\n')

    # Return the message to the main consumer orchestrator to handle the message.    
    socontra.agent_return(agent_name, request_message_consumer, received_message=received_message)


@route('cancel_order', 'service', 'transact', 'consumer')  
# -> response: end the dialogue/transaction (unsuccessful exit) -> optionally start new task request to find an alternative supplier to achieve the task.
def cancel_order_consumer(agent_name: str, received_message: Message, message_responding_to: Message):    
    # The Socontra standard transact protocol.
    # Consumer agent
    # The supplier canceled the order that was agreed to or purchased.

    # Protocol validation.
    if not socontra.protocol_validation(agent_name, received_message, message_responding_to, valid_message_types=['accept_offer', 'request_message']):
        return
    
    print('\nOrder was canceled by the supplier ', received_message.sender_name, ' which was ', received_message.order, '. The reason is ', received_message.message, '\n')

    # Return the message back to the main consumer orchestrator to close out the dialogue/transaction and initiate any replanning.
    socontra.agent_return(agent_name, cancel_order_consumer, received_message=received_message)


@route('order_complete', 'service', 'transact', 'consumer')
# -> response: if sign-off not required: end the dialogue/transaction (successful exit) 
#              else: socontra.order_confirm_success or socontra.order_confirm_fail
def order_complete_consumer(agent_name: str, received_message: Message, message_responding_to: Message):
    # The Socontra standard transact protocol.
    # Consumer agent
    # The supplier has completed and/or delivered the order to fulfill the task for the consumer.

    # Protocol validation.
    if not socontra.protocol_validation(agent_name, received_message, message_responding_to, valid_message_types=['accept_offer', 'request_message']):
        return
    
    # To support protocol control/logic, we can 'close messages' which are no longer valid as we progress through the protocol.
    # We can also socontra.close_agents() if we want to stop a dialogue with a specific agent.
    socontra.close_message(agent_name, close_message_type=['cancel_order', 'order_failed', 'order_complete', 'request_message'], message_responding_to=received_message)
    
    print('\nOrder to fulfill task has been completed by ', received_message.sender_name, '. The (purchase) order was ', received_message.order, 
          ' and completion message is ', received_message.message, '\n')
     
     # Return the message back to the main consumer orechestrator to assess if sign-off is required, and end the dialogue/transaction.
    socontra.agent_return(agent_name, order_complete_consumer, received_message=received_message)


@route('order_failed', 'service', 'transact', 'consumer')  
# -> response: end the dialogue/transaction (unsuccessful exit) -> optionally start new task request to find an alternative supplier to achieve the task.
def order_failed_consumer(agent_name: str, received_message: Message, message_responding_to: Message):    
    # The Socontra standard transact protocol.
    # Consumer agent
    # The supplier could not execute or deliver on the order that was agreed to or purchased.

    # Protocol validation
    if not socontra.protocol_validation(agent_name, received_message, message_responding_to, valid_message_types=['accept_offer', 'request_message']):
        return
    
    print('\nOrder could not be fulfilled by the supplier ', received_message.sender_name, ' which was ', received_message.order, '. The reason is ', received_message.message, '\n')

    # Return the message back to the main consumer orchestrator to close out the dialogue/transaction and initiate any replanning.
    socontra.agent_return(agent_name, order_failed_consumer, received_message=received_message)


# CONSUMER ORCHESTRATOR FOR TRANSACT PROTOCOL

def transact_orchestrator_consumer(agent_name, task, distribution_list, proposal_timeout, invite_offer_timeout):
    # Example orchestrator for the transact protocol.
    # Consumer endpoints contain socontra.agent_return() to return messages back to this orchestrator to manage.

    # Send the task announcement using the 'transact' protocol.
    network_response = socontra.new_request(agent_name, distribution_list=distribution_list, task=task, proposal_timeout=proposal_timeout, protocol='transact')

    ## SEARCH AND EVALUATION STAGE. 
    ordered_list_of_proposals = search_and_evaluation(agent_name, proposal_timeout)

    ## SELECTION AND COMMITMENT STAGE - CREATE AN ORDER.
    order_confirmed = selection_and_commitment(agent_name, ordered_list_of_proposals, invite_offer_timeout, network_response.message)

    ## ORDER MONITORING/TRACKING AND DELIVERY STAGE.
    if order_confirmed:
        # Returns True if successful, False otherwise.
        return execution_monitoring_and_delivery(agent_name)
    else:
        # Order could not be found. Unsuccessful exit.
        return False


def search_and_evaluation(agent_name, proposal_timeout):
    ## SEARCH AND EVALUATION STAGE.

    # Wait for proposals, and evaluate each one. Store proposals in an ordered list ordered by cost/quality.
    start_time = time.time()
    ordered_list_of_proposals = []
    counter = 1

    while True:
        current_time = time.time()
        time_to_wait_for_proposals = max(proposal_timeout - (current_time - start_time), 0.0)

        # Wait for offers to be received.
        proposal_returned = socontra.expect(agent_name, receive_proposal, timeout=time_to_wait_for_proposals)

        if proposal_returned == None:
            # No more offers, and timeout expired.
            break
        else:
            # Get the offer (message) component of the agent_return dict.
            proposal = proposal_returned['received_message']

        counter +=1

        proposal_cost = evaluate_proposal_cost(proposal)

        # Add the proposal to the ordered list of proposals as a tuple (proposal_cost, proposal).
        # The lowest cost (best) proposal will be placed at the head of the list.
        insort(ordered_list_of_proposals, (proposal_cost, counter, proposal))

    return ordered_list_of_proposals


def selection_and_commitment(agent_name, ordered_list_of_proposals, invite_offer_timeout, original_request_message):
    ## SELECTION AND COMMITMENT STAGE - CREATE AN ORDER.

    order_confirmed = False

    # Now that we have an ordered list of proposals, lets select the top one, and if that fails, the next best one, and so on.
    while ordered_list_of_proposals:
        
        # Best proposal is at the head of the ordered list. 
        best_proposal = ordered_list_of_proposals.pop(0)[2]

        # Send an invite offer (aka 'add item to cart') message to allow the supplier to send a formal binding offer for the proposal.
        socontra.invite_offer(agent_name, message_responding_to=best_proposal, invite_offer_timeout=invite_offer_timeout)

        # Wait for the response from the supplier.
        message_type, invite_offer_response = socontra.expect_multiple(agent_name, [receive_offer, reject_invite_offer_consumer], timeout=invite_offer_timeout)

        # If the supplier does not respond or rejects the invite offer, then try the next proposal.
        if message_type == None or message_type == 'reject_invite_offer_consumer':
            continue

        offer = invite_offer_response['received_message']

        # If payment is required, get payment details and human_authorization if required.
        if offer.payment_required:
            
            # If human authorization is required by either the supplier or the consumer itself...
            if offer.human_authorization_required or consumer_requires_authorization():
                human_authorization = get_human_authorization(agent_name, offer)

                if not human_authorization:
                    # Human rejected the offer. Send the supplier a reject offer message and try next proposal.
                    socontra.reject_offer(agent_name, message_responding_to=offer)
                    continue
            
            # Human authorization not required.
            else:
                human_authorization = False
            
            # Get payment details.
            payment = get_payment_details(agent_name)
        else:
            payment, human_authorization = None, None

        # A final check to make sure the offer has not been revoked or timeout expired.
        if socontra.timeout_not_expired(offer.offer_timeout) and \
            socontra.expect(agent_name, revoke_offer_consumer, timeout=0) is None:

            # Accept the offer.
            socontra.accept_offer(agent_name, message_responding_to=offer, payment=payment, human_authorization=human_authorization)

            # Wait for payment confirmation if payment required.
            if offer.payment_required:
                message_type, invite_offer_response = socontra.expect_multiple(agent_name, [payment_confirmed_consumer, payment_error_consumer], timeout=60)

                # If no response or payment error, then in this example, we will try another proposal.
                if message_type == None or message_type == 'payment_error_consumer':
                    continue
            
            # Payment has been confirmed. We have a mutually binding order. Can now wait for the supplier to complete and deliver the order.
            order_confirmed = True
            break

        # Loop back to try another proposal.

    if not order_confirmed:
        # Could not find a successful solution. Replan and/or exit the dialogue/transaction.
        # Use best_proposal as a message to pass to socontra to close out.
        return unsuccessful_exit(agent_name, original_request_message)

    # To support protocol control/logic, we can 'close messages' which are no longer valid as we progress through the protocol.
    # We can also socontra.close_agents() if we want to stop a dialogue with a specific agent.
    # Close out protocol messages.
    socontra.close_message(agent_name, close_message_type=['offer', 'reject_invite_offer', 'revoke_offer', 'proposal', 'reject_task'], message_responding_to=offer)

    return True

def execution_monitoring_and_delivery(agent_name):
    ## ORDER MONITORING/TRACKING AND DELIVERY STAGE.

    # We can now wait for messages, that could be: request_message (information about the task or it execution), 
    # cancel_order (from supplier), complete_success or complete_fail.
    # Could also monitor and track the order, and cancel it (socontra.cancel_order()) if not progressing to plan (excluded from this example demo).
    while True:
        message_type, order_message_returned = socontra.expect_multiple(agent_name, [cancel_order_consumer, order_complete_consumer, order_failed_consumer, request_message_consumer])
        order_message = order_message_returned['received_message']
        
        # Process any messages to complete the task from the supplier.
        if message_type == 'request_message_consumer':
            response = process_supplier_agent_message(order_message)
            if response is not None:
                socontra.request_message(agent_name, message=response, message_responding_to=order_message, recipient_type='supplier')

        # Order is canceled by the supplier. Exit unsuccessfully and try again.
        elif message_type == 'cancel_order_consumer' or message_type == 'order_failed_consumer':
            # Perform any recovery tasks for unsuccessful exit, such as replanning, or request the same or new task.
            return unsuccessful_exit(agent_name, order_message)
        
        # Order is complete.
        elif message_type == 'order_complete_consumer':
            if order_delivered_successfully(order_message):
                # Sign-off on the order completion.
                socontra.order_confirm_success(agent_name, message='Thank you, much appreciated.', message_responding_to=order_message)

                # Perform any finalization or wrap up tasks and successfully exit.
                successful_exit(agent_name, order_message)
            
            else:
                # Let the supplier agent know that the order not completed/delivered successfully as promised.
                socontra.order_confirm_fail(agent_name, message='You multiplied the numbers rather than added them.', message_responding_to=order_message)
                return unsuccessful_exit(agent_name, order_message)
        
        # Ignore other messages for this task.
        else:
            pass

        
def evaluate_proposal_cost(proposal):
    # Function should evaluate the cost of the proposal so that the agent can compare and select (invite offer) the best proposal.
    # The cost in this example is an int in offer.message.
    return proposal.proposal['cost']
        
def process_supplier_agent_message(order_message):
    # Process any messages and respond if required. 
    # In this example, the supplier is asking for two numbers to add. Return the numbers.
    return {'a': 4, 'b': 5}

def order_delivered_successfully(order_message):
    # Function to check if the order was successfully delivered.
    # Delivery of the order that was promised/purchased is different to whether the delivered order achieved tha task.
    # Print the result.
    print('\nFinal result is ', order_message.message, ' which is correct.\n')
    return True

def task_achieved():
    # Function to check if the task has now been acheived by the completed order.
    # If not, may need to replan.
    return True

def get_human_authorization(agent_name, offer):
    # Get human authorization for the offer and return True if human accepts payment for the offer, and False otherwise.
    pass
    return True

def get_payment_details(agent_name):
    # Get payment details or method that will allow the supplier agent to make the purchase.
    pass
    return {'card_number': 'xxxx xxxx xxxx xxxx',
            'secondary_payment': 'hugs'}

def consumer_requires_authorization(agent_name, offer):
    # The consumer requires (or has requested) authorization before purchase.
    # Could be for any purchase, or purchases of a certain type or amount etc.
    pass
    return True

def unsuccessful_exit(agent_name, a_dialogue_message):
    # Could not find a successful solution. Replan and/or exit the dialogue/transaction.
    print('Agent ', agent_name, ' exiting unsuccessfully.')
    pass

    # End the dialogue for this process.
    socontra.close_dialogue(agent_name, a_dialogue_message)
    return False

def successful_exit(agent_name, a_dialogue_message):
    # Order completed and request completed successfully.
    # Perform any finalization tasks.
    print('Agent ', agent_name, ' exiting successfully!')
    pass

     # End the dialogue for this process.
    socontra.close_dialogue(agent_name, a_dialogue_message)
    return True
