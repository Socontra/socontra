# Socontra template for the 'allocate' protcol, suitable for automated agent-to-agent non-commercial transactions: task allocation.
# Protocol for the consumer of services.

import time

from socontra.socontra import Socontra, Message, Protocol

# Create a Socontra Client for the agent.
protocol = Protocol()
socontra: Socontra = protocol.socontra
def route(*args):
    def inner_decorator(f):
        protocol.route_map[(args)] = f
        return f
    return inner_decorator



# ----- SOCONTRA SERVICES PROTOCOL: 'allocate' - allocation of a task to agents  -------------------------------------


@route('offer', 'service', 'allocate', 'consumer')  
# -> response: socontra.accept_offer(), socontra.reject_offer(), socontra.task_withdrawn(), 
# or NoComms and end protocol (offer will timeout by received_message.offer_timeout)
def receive_offer(agent_name: str, received_message: Message, message_responding_to: Message):
    # The Socontra standard allocate protocol.
    # Consumer agent
    # The supplier has submitted a committed and binding 'offer' to fulfill the consumer's task.
    # This is like 'add to cart' for online stores - so item is added to the cart and ready for purchase.
    # If the consumer accepts the offer, it becomes a mutually binding contract or 'purchase' for the services (or product), and which time 
    # the offer becomes an 'order' to be executed and delivered by the supplier (agent).

    # Protocol validation. Messages are only valid if the previous message in the dialogue (message_responding_to) was 'new_task_request'.
    if not socontra.protocol_validation(agent_name, received_message, message_responding_to, valid_message_types=['new_task_request']):
        return
        
    # Agent response
    print(f'\nOffer to fulfill the task was submitted by  {received_message.sender_name}. The offer is {received_message.offer}\n')

    # Return the offer to the consumer agent orchestrator to evaluate and decide to accept or reject.
    socontra.agent_return(agent_name, receive_offer, received_message=received_message)
    

@route('reject_task', 'service', 'allocate', 'consumer')  
# -> response: protocol/dialogue end if no suitable offers, or do nothing if other offers received.
def reject_task_consumer(agent_name: str, received_message: Message, message_responding_to: Message):    
    # The Socontra standard allocate protocol.
    # Consumer agent
    # Supplier sent a reject task message to the consumer.
    # This means the supplier officially declines to send an offer to fulfill the task.

    # Protocol validation. Messages are only valid if the previous message in the dialogue (message_responding_to) was 'new_task_request'.
    if not socontra.protocol_validation(agent_name, received_message, message_responding_to, valid_message_types=['new_task_request']):
        return
    
    # Agent response
    print('\nSupplier rejected to submit an offer to fulfill task ', received_message.task, '. The supplier is ', received_message.sender_name, '. The reason/message is ', received_message.message, '\n')

    # In our example, we just ignore reject_task messages. We do not return this message to the orchestrator (unnecessary).


@route('request_message', 'service', 'allocate', 'consumer')  
# -> response: NoComms (wait until order complete), socontra.request_message() (provide more info to complete order) or socontra.cancel_order()
def request_message_consumer(agent_name: str, received_message: Message, message_responding_to: Message):
    # The Socontra standard allocate protocol.
    # Consumer agent
    # Supplier sent a message to the consumer.
    # These messages can be used for sending messages between consumer and supplier necessary to complete the order in order to fulfill/achieve the task.

    # Protocol validation.
    if not socontra.protocol_validation(agent_name, received_message, message_responding_to, valid_message_types=['accept_offer', 'request_message']):
        return

    # Agent response
    print('\n', received_message.sender_name, ' sent a message relating to the order, which is ', received_message.message, '\n')
    
    # Return the message to the comsumer orchestrator to handle.
    socontra.agent_return(agent_name, request_message_consumer, received_message=received_message)


@route('cancel_order', 'service', 'allocate', 'consumer')  
# -> response: unsuccessful exit -> start new protocol/dialogue to find an alternative agent to fulfill task.
def cancel_order_consumer(agent_name: str, received_message: Message, message_responding_to: Message):    
    # The Socontra standard allocate protocol.
    # Consumer agent
    # The supplier canceled the order that was agreed to or purchased.

    # Protocol validation
    if not socontra.protocol_validation(agent_name, received_message, message_responding_to, valid_message_types=['accept_offer', 'request_message']):
        return
    
    # Agent response
    print('\nOrder was canceled by the supplier ', received_message.sender_name, ' which was ', received_message.order, '. The reason/message is ', received_message.message, '\n')

    socontra.agent_return(agent_name, cancel_order_consumer, received_message=received_message)


@route('order_complete', 'service', 'allocate', 'consumer')  
# -> response: order sign-off (optional), so either socontra.order_confirm_success or socontra.order_confirm_fail.
def order_complete_consumer(agent_name: str, received_message: Message, message_responding_to: Message):
    # The Socontra standard allocate protocol.
    # Consumer agent
    # The supplier has completed and/or delivered the order to fulfill the task for the consumer.

    # Protocol validation.
    if not socontra.protocol_validation(agent_name, received_message, message_responding_to, valid_message_types=['accept_offer', 'request_message']):
        return
    
    # To support protocol control/logic, we can 'close messages' which are no longer valid as we progress through the protocol.
    # We can also socontra.close_agents() if we want to stop a dialogue with a specific agent.
    socontra.close_message(agent_name, close_message_type=['cancel_order', 'order_failed', 'order_complete', 'request_message'], message_responding_to=received_message)
    
    # Agent response
    print('\nOrder to fulfill task has been completed by ', received_message.sender_name, '. The (purchase) order was ', received_message.order, 
          ' and completion message is ', received_message.message, '\n')
     
    # Return the message so that the consumer orchestrator can handle it.
    socontra.agent_return(agent_name, order_complete_consumer, received_message=received_message)


@route('order_failed', 'service', 'allocate', 'consumer')  
# -> response: unsuccessful exit -> start new protocol/dialogue to find an alternative agent to fulfill task.
def order_failed_consumer(agent_name: str, received_message: Message, message_responding_to: Message):    
    # The Socontra standard allocate protocol.
    # Consumer agent
    # The supplier could not execute or deliver on the order that was agreed to or purchased.

    # Protocol validation.
    if not socontra.protocol_validation(agent_name, received_message, message_responding_to, valid_message_types=['accept_offer', 'request_message']):
        return
    
    # Agent response
    print('\nOrder could not be fulfilled by the supplier ', received_message.sender_name, ' which was ', received_message.order, '. The reason/message is ', received_message.message, '\n')

    # Return the message so that the consumer orchestrator can handle it.
    socontra.agent_return(agent_name, order_failed_consumer, received_message=received_message)



# CONSUMER ORCHESTRATOR FOR ALLOCATE PROTOCOL

def allocate_orchestrator_consumer(agent_name, task, distribution_list, timeout):
    # Example orchestrator for the allocate protocol.
    # Consumer endpoints contain socontra.agent_return() to return messages back to this orchestrator to manage.

    # Send the task announcement using the 'allocate' protocol.
    socontra.new_request(agent_name, distribution_list=distribution_list, task=task, proposal=task, invite_offer_timeout=timeout, protocol='allocate')

    # Wait for offers, and evaluate each one. Keep the best offer and reject the worst offers iteratively as they are received.
    start_time = time.time()
    best_offer = None
    best_offer_cost = None

    while True:
        current_time = time.time()
        time_to_wait_for_offers = max(timeout - (current_time - start_time), 0.0)

        # Wait for offers to be received.
        offer_returned = socontra.expect(agent_name, receive_offer, timeout=time_to_wait_for_offers)

        if offer_returned == None:
            # No more offers, and timeout expired.
            break
        else:
            # Get the offer (message) component of the agent_return dict.
            offer = offer_returned['received_message']

        offer_cost = evaluate_offer_cost(offer)

        # First offer is the best offer so far.
        if best_offer is None:
            best_offer = offer
            best_offer_cost = offer_cost
        
        # Else, if new received offer is better (lower cost) that the current best offer, reject the current 'best offer' and the
        # new received offer becomes the best offer.
        elif offer_cost < best_offer_cost:
            socontra.reject_offer(agent_name=agent_name, message_responding_to=best_offer, message='I have cheaper options, thanks anyway')
            best_offer = offer
            best_offer_cost = offer_cost

        # Otherwise, reject the new received offer as it is no better than the current best offer.
        else:
            socontra.reject_offer(agent_name=agent_name, message_responding_to=offer, message='I have cheaper options, thanks anyway')

    # We now have the best offer from a supplier agent, which can be accepted.
    socontra.accept_offer(agent_name, best_offer)

    # To support protocol control/logic, we can 'close messages' which are no longer valid as we progress through the protocol.
    # We can also socontra.close_agents() if we want to stop a dialogue with a specific agent.
    # Close any more messages from other agents regarding offers or task rejection.
    socontra.close_message(agent_name, close_message_type=['offer', 'reject_task'], message_responding_to=best_offer)

    # We can now wait for messages, that could be: request_message (information about the task or it execution), cancel_order,
    # complete_success or complete_fail.
    while True:
        message_type, order_message_returned = socontra.expect_multiple(agent_name, [cancel_order_consumer, order_complete_consumer, order_failed_consumer, request_message_consumer])
        order_message = order_message_returned['received_message']
        
        if message_type == 'request_message_consumer':
            response = process_supplier_agent_message(order_message)
            if response is not None:
                socontra.request_message(agent_name, message=response, message_responding_to=order_message, recipient_type='supplier')
        elif message_type == 'cancel_order_consumer' or message_type == 'order_failed_consumer':
            # Perform any recovery tasks for unsuccessful exit, such as replanning, or request the same or new task.
            pass
            break
        elif message_type == 'order_complete_consumer':
            if order_delivered_successfully(order_message):
                # Sign-off on the order completion.
                socontra.order_confirm_success(agent_name, message='Thank you, much appreciated.', message_responding_to=order_message)

                # Can now check if the task was successfully achieved by the completed order.
                # I.e. did the order actually achieve the task that it was intended to fulfill.
                if not task_achieved():
                    # Task not achieved by the order (or partially achieved). May need to replan and perform any recovery tasks.
                    pass                    
            else:
                # Let the supplier agent know that the order not completed/delivered successfully as promised.
                socontra.order_confirm_fail(agent_name, message='Thank you, much appreciated.', message_responding_to=order_message)

                # Perform any recovery tasks for unsuccessful exit, such as replanning, or request the same or new task.
                pass
            break
        else:
            # Ignore other messages for this task.
            pass
            
    # End the dialogue for this process and return.
    socontra.close_dialogue(agent_name, order_message)
        
def evaluate_offer_cost(offer):
    # Function should evaluate the cost of the offer so that the agent can compare and select the best offer.
    # The cost in this example is an int in offer.message.
    offer_cost = offer.offer['cost']
    print(f'\nAgent {offer.sender_name} offered to fulfill the task at a cost of {offer_cost}')
    return offer_cost
        
def process_supplier_agent_message(order_message):
    # Process any messages and respond if required. 
    # In this example, the supplier is asking for two numbers to add. Return the numbers.
    return {'a': 4, 'b': 5}

def order_delivered_successfully(order_message):
    # Function to check if the order was successfully delivered.
    # Print the result.
    print('\nFinal result is ', order_message.message, ' which is correct.\n')
    return True

def task_achieved():
    # Function to check if the task has now been achieved by the completed order.
    # Successful completion and delivery of the order is different to whether the delivered order achieved the task.
    # If not, may need to replan.
    return True









   