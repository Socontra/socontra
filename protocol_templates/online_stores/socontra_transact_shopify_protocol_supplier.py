# Socontra template protocol configuration to create a Shopify online store Web Agent.
# Adapts Socontra's 'transact' protocol (protocol_templates/service/socontra_transact_protocol_supplier.py), 
# suitable for automated agent-to-agent commercial transactions. Uses Shopify APIs to automate aspects of the 
# purchase process.
# NOTE - Shopify does not (yet) allow automated purchase of products. The checkout step of making a
#          purchase of items in the cart must be completed manually by the agent's human user.

import time
import requests, json
from pprint import pprint
from datetime import datetime, timedelta, timezone

import config_shopify

from socontra.socontra import Socontra, Message, Protocol

# Create a Socontra Client for the agent.
protocol = Protocol()
socontra:Socontra = protocol.socontra
def route(*args):
    def inner_decorator(f):
        protocol.route_map[(args)] = f
        return f
    return inner_decorator


# ----- SOCONTRA SHOPIFY PROTOCOL TEMPLATE  -------------------------------------

@route('new_task_request', 'service', 'transact', 'supplier')  
# -> response: socontra.reject_task(), socontra.submit_proposal(), or NoComms and end protocol (task will timeout by received_message.proposal_timeout)
def new_task_request(agent_name: str, received_message: Message):
    # The Socontra standard transact protocol.
    # Supplier agent
    # The supplier receives a new task request to be fulfilled by the consumer.
    # This is equilavent to a 'product search' in online stores.
    
    print(f'\nNew request to fulfill task from {received_message.sender_name}. The task is {received_message.task} requires a response by {socontra.get_deadline(received_message.proposal_timeout)}\n')
  
    # Conduct a search, if the supplier agent is able to fulfill the task. Get the top search result(s).
    proposal_list = service_or_product_search(received_message.task)
    
    if proposal_list is not None:
        # Search results found one or more suitable services or products that can fulfill the task.
        # Return the proposal(s) to the consumer (all in one message). 
        socontra.submit_proposal(agent_name, proposal=proposal_list, message_responding_to=received_message)
    else:
        # Close the dialogue/interaction with the agent.
        socontra.close_dialogue(agent_name, received_message)


@route('reject_proposal', 'service', 'transact', 'supplier')  
# -> response: end the dialogue/transaction with the consumer for the specific task. 
#    Optionally, the supplier could submit another proposal, if the protocol and timeout expiry allows.
def reject_proposal_supplier(agent_name: str, received_message: Message, message_responding_to: Message):    
    # The Socontra standard transact protocol.
    # Supplier agent
    # The consumer 'rejected the proposal' submitted to the supplier.
    # This message is optional, and can be used to inform the supplier that the offer was not suitiable and to submit another 
    # if time allows (i.e. reject_proposal implies return more search results).

    # Protocol validation
    if not socontra.protocol_validation(agent_name, received_message, message_responding_to, valid_message_types=['proposal']):
        return
    
    print('\nProposal rejected for task ', received_message.task, ' by ', received_message.sender_name, '. The reason/message is ', received_message.message, '\n')

    # End dialogue.
    socontra.close_dialogue(agent_name, received_message)


@route('invite_offer', 'service', 'transact', 'supplier')  
# -> response: socontra.submit_offer() (with an optional socontra.revoke_offer() following submission, if required), 
#              socontra.reject_invite_offer(), or NoComms (invite offer will timeout by received_message.invite_offer_timeout)
def receive_invite_offer(agent_name: str, received_message: Message, message_responding_to: Message):
    # The Socontra standard transact protocol.
    # Supplier agent
    # The consumer has sent an invite offer request asking the supplier to submit the proposal as a formal binding offer.
    # This is equivalent to the consumer requesting that the supplier "add item to cart" in online stores.
    # If the offer is sent via socontra.submit_offer(), that is equivalent to informing the consumer "item was added to cart".

    # Protocol validation.
    if not socontra.protocol_validation(agent_name, received_message, message_responding_to, valid_message_types=['proposal']):
        return
    
    print('\nInvite to offer for proposal ', received_message.proposal, ' was received by  ', agent_name, ' from ', received_message.sender_name, ' requires a response by ',
          socontra.get_deadline(received_message.invite_offer_timeout), '\n')
    
    # Add the item/product(s) to the cart, and submit the binding/committed offer to the consumer.
    offer = add_items_to_cart(received_message, received_message.invite_offer_timeout)

    # Timeout for the cosumer to accept the offer and make the purchase.
    timeout = 20
    # Submit the offer to the consumer. Assume payment and human authorization for the purchase is required.
    socontra.submit_offer(agent_name, offer=offer, message_responding_to=received_message, 
                              offer_timeout=timeout, payment_required = True, human_authorization_required = True)


@route('accept_offer', 'service', 'transact', 'supplier')  
# -> response:  If payment for services required: socontra.payment_confirmed() or socontra.payment_denied()
#               Else: socontra.request_message() (info exchange to complete order) or socontra.cancel() (to cancel the order) or 
#                     order completion/delivery messages: socontra.order_complete() or socontra.order_failed()
def accept_offer_supplier(agent_name: str, received_message: Message, message_responding_to: Message, payment: str | dict, human_authorization: bool | str | dict):
    # The Socontra standard transact protocol.
    # Supplier agent
    # The consumer has 'accepted the offer' for the supplier to fulfill the task.
    # This message is equilavent to 'purchase item in cart' with online stores.

    # Shopify does not provide a way for automated purchasing. Therefore, this agent returns the Shopify URL to the 
    # checkout to allow the agent's owner to manually make the purchase, aand then return to the agent interaction
    # for verification of the purchase.

    # Protocol validation.
    if not socontra.protocol_validation(agent_name, received_message, message_responding_to, valid_message_types=['offer', 'payment_error']):
        return
    
    print('\nOffer accepted to fulfill task by ', received_message.sender_name, '. The (purchase) order is ', received_message.order, '\n')

    # In case of payment errors, set a timeout for the consumer agent to respond with another accept_offer to resolve the issue.
    timeout = 60

    # Get the checkout URL.
    shopify_checkout_url = get_shopify_checkout_url(received_message.offer)

    # Store the current time, used to verify the purchase order.
    time_start_manual_purchase = datetime.now(timezone.utc)

    # Send a general message to the consumer agent with the url.
    socontra.request_message(agent_name, message=shopify_checkout_url, message_responding_to=received_message, recipient_type='consumer')

    # Wait until the consumer responds saying that the consumer has completed the purchase.
    consumer_response_message = socontra.expect(agent_name, confirm_manual_purchase)

    # Now check if the order has gone through. Check the order via the Admin API and  the consumer email address, and check
    # if an order by the agent was made after time time_start_manual_purchase.
    if consumer_response_message['received_message'].message['shopify_checkout_url']:
        # Verify the order was created, and thus paid for.
        order_verification, message, order_name, order_details = verify_order_created(agent_name, received_message, time_start_manual_purchase)

        # If the order was not verified (not found or fully paid), then exit.
        if not order_verification:
            # Order was not verified (could not be found). Send a payment error and see if the consumer agent can retry
            # and send a follow up 'accept offer'.
            socontra.payment_error(agent_name, message = message, offer_timeout=timeout, message_responding_to=received_message)
            return
        elif order_verification:
            # Order confirmed and paid. Send the consumer agent a message saying that payment confirmed.
            socontra.payment_confirmed(agent_name, order=order_details, message = message, message_responding_to=received_message)
    else:
        # Order was not confirmed, so remove the item from cart and return.
        remove_item_from_cart(consumer_response_message['received_message'].offer)

        # End the dialogue/transaction.
        socontra.close_dialogue(agent_name, received_message)
        return

    # To support protocol control/logic, we can 'close messages' which are no longer valid as we progress through the protocol.
    # The order is now in place. Close protocol messages that are no longer relevant.
    socontra.close_message(agent_name, close_message_type=['invite_offer', 'reject_proposal', 'task_withdrawn', 'reject_offer', 'accept_offer'], message_responding_to=received_message)

    # Complete and deliver the order, and send completion messages when done.
    complete_and_deliver_order(agent_name, received_message, order_name)


@route('reject_offer', 'service', 'transact', 'supplier')  
# -> response: end dialogue/transaction, or (optionally) submit an alternative proposal
def reject_offer_supplier(agent_name: str, received_message: Message, message_responding_to: Message):    
    # The Socontra standard transact protocol.
    # Supplier agent
    # The consumer 'rejected the offer' to fulfill the task for the consumer.

    # Protocol validation
    if not socontra.protocol_validation(agent_name, received_message, message_responding_to, valid_message_types=['offer']):
        return
    
    # Agent response
    print('\nOffer rejected to fulfill task ', received_message.task, ' by ', received_message.sender_name, '. The reason/message is ', received_message.message, '\n')

    # Remove item from cart.
    remove_item_from_cart(received_message.offer)

    # End the dialogue/transaction.
    socontra.close_dialogue(agent_name, received_message)

@route('confirm_manual_purchase', 'service', 'transact', 'supplier')  
# -> response: socontra.request_message() (reply to message), socontra.cancel_order(), socontra.order_complete(), socontra.order_failed()
def confirm_manual_purchase(agent_name: str, received_message: Message, message_responding_to: Message):
    # Supplier agent
    # Consumer sent a message to the supplier saying that the manual purchase was confirmed on the consumer side, and
    # want the supplier to verify the purchase on the Supplier (Shopify) side.

    # Protocol validation
    if not socontra.protocol_validation(agent_name, received_message, message_responding_to, valid_message_types=['offer', 'payment_confirmed', 'request_message']):
        return
    
    socontra.agent_return(agent_name, confirm_manual_purchase, received_message=received_message)


@route('request_message', 'service', 'transact', 'supplier')  
# -> response: socontra.request_message() (reply to message), socontra.cancel_order(), socontra.order_complete(), socontra.order_failed()
def request_message_supplier(agent_name: str, received_message: Message, message_responding_to: Message):
    # The Socontra standard protocol.
    # Supplier agent
    # Consumer sent a message to the supplier
    # These messages can be used for sending messages between consumer and supplier necessary to complete the order in order to fulfill/achieve the task.

    # Protocol validation
    if not socontra.protocol_validation(agent_name, received_message, message_responding_to, valid_message_types=['offer', 'payment_confirmed', 'request_message']):
        return

    print('\n', received_message.sender_name, ' sent a message relating to the order, which is ', received_message.message, '\n')
 
    # Return the response to the supplier function that is executing and delivering the order.
    socontra.agent_return(agent_name, request_message_supplier, received_message=received_message)


@route('cancel_order', 'service', 'transact', 'supplier')  
# -> response: end dialogue/transaction.
def cancel_order_supplier(agent_name: str, received_message: Message, message_responding_to: Message):    
    # The Socontra standard transact protocol.
    # Supplier agent
    # The consumer canceled the order that was agreed to or purchased.

    # Will be handled in future versions.

    # Protocol validation
    if not socontra.protocol_validation(agent_name, received_message, message_responding_to, valid_message_types=['offer', 'request_message']):
        return
    
    # Agent response
    print('\nOrder was canceled by the consumer ', received_message.sender_name, ' which was ', received_message.order, '. The reason/message is ', received_message.message, '\n')

    # End the dialogue/transaction.
    socontra.close_dialogue(agent_name, received_message)


@route('confirm_success', 'service', 'transact', 'supplier') 
# -> response: end the dialogue/transaction (successful exit)
def order_complete_confirm_success(agent_name: str, received_message: Message, message_responding_to: Message):
    # The Socontra standard allocation protocol.
    # Supplier agent
    # The consumer has provided a 'sign-off' that the completed/delivered order was in fact completed satisfactorily.   

    # Protocol validation
    if not socontra.protocol_validation(agent_name, received_message, message_responding_to, valid_message_types=['order_complete']):
        return
    
    # Agent response
    print('\nSign-off for completed/delivered order has been received by the consumer: ', received_message.sender_name, '. Feedback is:', received_message.message, '\n')

    # Send the message back to the main supplier function that is executing and delivering on the order to perform
    # any finialization and wrap up tasks, and close out the dialogue/transaction.
    socontra.agent_return(agent_name, order_complete_confirm_success, received_message=received_message)


@route('confirm_fail', 'service', 'transact', 'supplier') 
# -> response: end the dialogue/transaction (unsuccessful exit)
def order_complete_confirm_fail(agent_name: str, received_message: Message, message_responding_to: Message):
    # The Socontra standard allocation protocol.
    # Supplier agent
    # This supplier has been notified that the consumer did provided a 'sign-off' for the completed/delivered order, because it was 
    # not completed or delivered satisfactorily.    

    # Protocol validation
    if not socontra.protocol_validation(agent_name, received_message, message_responding_to, valid_message_types=['order_complete']):
        return
    
    print('\nConsumer ', received_message.sender_name, ' did not sign-off on the completed/delivered order. Feedback is:', received_message.message, '\n')

    # Send the message back to the main supplier function that is executing and delivering on the order to perform
    # any order resolution actions, before closing out the dialogue/transaction.
    socontra.agent_return(agent_name, order_complete_confirm_success, received_message=received_message)


@route('task_withdrawn', 'service', 'transact', 'supplier')  
# -> response: end the dialogue/transaction
def task_withdrawn_supplier(agent_name: str, received_message: Message, message_responding_to: Message):
    # The Socontra standard allocation protocol.
    # Supplier agent
    # This supplier has been notified that the consumer has withdrawn the task request. This concludes the transaction/dialogue.

    # Protocol validation
    if not socontra.protocol_validation(agent_name, received_message, message_responding_to, valid_message_types=['offer']):
        return
    
    print('\nConsumer ', received_message.sender_name, ' has withdrawn the task request. Message is:', received_message.message, '\n')

    # End the dialogue/transaction.
    socontra.close_dialogue(agent_name, received_message)


# Shopify functions to support the (transact) protocol


def service_or_product_search(task):
    # Run a search on the database for services, products or resources that can to fulfill the task.

    # Go through each of the task items in task and run a search and return the results.
    products_to_return = {'proposal_list' : []}
    
    for a_task in task['task']:
        products_to_return['proposal_list'].append(__single_service_or_product_search(a_task))

    print('----------------------------------------------')
    print('Product search\n')
    pprint(products_to_return)

    return products_to_return


def __single_service_or_product_search(a_task):
    # Run a product search query for a single task a_task.

    # Refer https://shopify.dev/docs/api/storefront/latest/queries/products for api fields.

    # Get the query to search for from variable task.
    product_search_query = a_task['product_search_query']
    max_products_to_return = a_task['number_proposals']
    quantity = a_task['quantity']

    # Call the Shopify API to return the search.
    query=f"""
            query {{
            products(first: {max_products_to_return}, query: "title:{product_search_query} OR displayName:{product_search_query} OR {product_search_query} AND status:ACTIVE AND available_for_sale:true", sortKey: RELEVANCE, reverse: false) {{
                edges {{
                node {{
                    id
                    title
                    handle
                    description
                    productType
                    vendor
                    totalInventory
                    priceRange {{
                    maxVariantPrice {{
                        amount
                        currencyCode
                    }}
                    minVariantPrice {{
                        amount
                        currencyCode
                    }}
                    }}

                    variants(first:5){{
                    edges {{
                        node {{
                        id
                        title
                        quantityAvailable
                        availableForSale
                        price {{
                            amount
                            currencyCode
                        }}
                        selectedOptions {{
                            name
                            value
                        }}
                        }}
                    }}
                    }}

                }}
                }}
            }}
            }}
        """

    payload = {'query': query}
    get_products = requests.post(f"https://{config_shopify.myshop_name}.myshopify.com/api/{config_shopify.api_version}/graphql.json", headers=config_shopify.header_values, json=payload)
    result=json.loads(get_products.content)
    products = result['data']['products']['edges']

    # Create the dict needed to return to the consumer.
    single_product_to_return = create_product_dict(products, quantity)

    # Return the results.
    return single_product_to_return


def create_product_dict(products, quantity):
    # Will take in the Shopify search results of the product query products, which is dict format, and 
    # Will create a dict to send back to the consumer agent.
    product_to_return = []

    # Go through each product returned.
    for a_product in products:
        product_dict = {}
        product_dict['title'] = a_product['node']['title']
        product_dict['description'] = a_product['node']['description']
        product_dict['vendor'] = a_product['node']['vendor']
        product_dict['productType'] = a_product['node']['productType']
        product_dict['variants'] = []
        variant_dict = {}
        # Return the variants and let the consumer assess it with its AI.
        for a_variant in a_product['node']['variants']['edges']:
            # Only include if product is for sale and there is sufficient quantity.
            # Also, only include if we want all variants or just a single one with specific id.
            if a_variant['node']['availableForSale'] and a_variant['node']['quantityAvailable'] >= quantity:
                variant_dict['variant_title'] = a_variant['node']['title']
                variant_dict['product_variant_id'] = a_variant['node']['id']
                variant_dict['product_variant_price_amount'] = a_variant['node']['price']['amount']
                variant_dict['product_variant_price_currency'] = a_variant['node']['price']['currencyCode']
                product_dict['variants'].append(variant_dict)
        
        # Only include the proposal if there is at least one variant (or instance) of the product.
        if product_dict['variants']:
            product_to_return.append(product_dict)

    return product_to_return


def create_offer_dict(single_proposal, product_to_add_to_cart_id, product_quantity):
    # Will extract the offer from the proposal, i.e. only include the variant relating to: product_to_add_to_cart_id.

    offer_to_return = {}

    for k,v in single_proposal.items():
        if k != 'variants':
            offer_to_return[k] = v

    offer_to_return['variants'] = {}

    for a_variant in single_proposal['variants']:
        if a_variant['product_variant_id'] == product_to_add_to_cart_id:
            for k,v in a_variant.items():
                offer_to_return['variants'][k] = v
            offer_to_return['variants']['product_quantity'] = product_quantity
            return offer_to_return
        else:
            continue


def add_items_to_cart(received_message : Message, timeout: int):
    # Go through each of the items in received_message.message and add the product-variant to the Shopify cart.
    # https://shopify.dev/docs/api/storefront/latest/mutations/cartcreate
    # The product ID to add to cart is in the variant and part of the message received from the consumer.

    lines_to_add_to_cart = ""
    offer = {'offer_list': []}

    for line_item_index_to_add in range(0, len(received_message.message['proposal_options_selected'])):
        product_to_add_to_cart_id = received_message.message['proposal_options_selected'][line_item_index_to_add]['variant_id']
        product_quantity = received_message.message['proposal_options_selected'][line_item_index_to_add]['quantity']

        lines_to_add_to_cart = lines_to_add_to_cart + f"""{{
                                                            merchandiseId: "{product_to_add_to_cart_id}",
                                                            quantity: {product_quantity},
                                                          }}, 
                                                        """
        
        offer['offer_list'].append(create_offer_dict(received_message.proposal['proposal_list'][line_item_index_to_add][received_message.message['proposal_options_selected'][line_item_index_to_add]['product_index']], 
                                                     product_to_add_to_cart_id, product_quantity))
    
    agent_owner_email = received_message.message['consumer_details']['email']
    country_code = get_country_code(received_message.message['consumer_details']['country'])
    first_name = received_message.message['consumer_details']['first_name']
    last_name = received_message.message['consumer_details']['last_name']
    phone = received_message.message['consumer_details']['mobile_number']
    address1 = received_message.message['consumer_details']['address_line_one']
    address2 = received_message.message['consumer_details']['address_line_two']
    city = received_message.message['consumer_details']['city']
    province = received_message.message['consumer_details']['state_province']
    zip_postal_code = received_message.message['consumer_details']['zip_postal_code']
    dialogue_id = received_message.dialogue_id
    message_id = received_message.message_id
    deliveryMethod = received_message.message['delivery_method']

    query_add_to_cart = f"""
            mutation {{
                cartCreate(
                input: {{
                    lines: [ {lines_to_add_to_cart} ],
                    # The information about the buyer that's interacting with the cart.
                    buyerIdentity: {{
                        email: "{agent_owner_email}",
                        countryCode: {country_code},
                        # An ordered set of delivery addresses associated with the buyer that's interacting with the cart. The rank of the preferences is determined by the order of the addresses in the array. You can use preferences to populate relevant fields in the checkout flow.
                        deliveryAddressPreferences: {{
                            # One-time use address isn't saved to the customer account after checkout
                            oneTimeUse: false,
                            deliveryAddress: {{
                                firstName: "{first_name}",
                                lastName: "{last_name}",
                                phone: "{phone}",
                                address1: "{address1}",
                                address2: "{address2}",
                                city: "{city}",
                                province: "{province}",
                                country: "{country_code}",
                                zip: "{zip_postal_code}"
                            }},
                        }},
                        preferences: {{
                            delivery: {{
                                deliveryMethod: {deliveryMethod}
                            }}
                        }},
                    }}
                    attributes: [
                        {{
                            key: "dialogue_message_id",
                            value: "{dialogue_id}"
                        }},
                        {{
                            key: "message_id",
                            value: "{message_id}"
                        }}
                    ]
                }}
                ) {{
                cart {{
                    id
                    createdAt
                    updatedAt
                    lines(first: 10) {{
                    edges {{
                        node {{
                        id
                        merchandise {{
                            ... on ProductVariant {{
                            id
                            }}
                        }}
                        }}
                    }}
                    }}
                    buyerIdentity {{
                    email,
                    phone,
                    deliveryAddressPreferences {{
                        __typename
                    }}
                    preferences {{
                        delivery {{
                        deliveryMethod
                        }}
                    }}
                    }}
                    attributes {{
                    key
                    value
                    }}
                    # The estimated total cost of all merchandise that the customer will pay at checkout.
                    cost {{
                    totalAmount {{
                        amount
                        currencyCode
                    }}
                    # The estimated amount, before taxes and discounts, for the customer to pay at checkout.
                    subtotalAmount {{
                        amount
                        currencyCode
                    }}
                    # The estimated tax amount for the customer to pay at checkout.
                    totalTaxAmount {{
                        amount
                        currencyCode
                    }}
                    # The estimated duty amount for the customer to pay at checkout.
                    totalDutyAmount {{
                        amount
                        currencyCode
                    }}
                    }}
                }}
                }}
            }}
    """

    payload = {'query': query_add_to_cart}
    result = requests.post(f"https://{config_shopify.myshop_name}.myshopify.com/api/{config_shopify.api_version}/graphql.json", headers=config_shopify.header_values, json=payload)
    result=json.loads(result.content)

    # Now add the cart ID and line item id to the offer to return to the consumer. 
    # We assume below there is only 1 item in the cart (position '0' in the list).
    offer['cart_id'] = result['data']['cartCreate']['cart']['id']
    offer['online_store'] = 'shopify'
    offer['consumer_details'] = received_message.message['consumer_details']
    offer['total_price'] = result['data']['cartCreate']['cart']['cost']['totalAmount']['amount']
    offer['currency'] = result['data']['cartCreate']['cart']['cost']['totalAmount']['currencyCode']

    # Add the product-variant line items for each item in the offer.
    add_cart_line_items(result, offer)
 
    print('-----------------------------------------------\n\n')
    print('Add product to cart')
    pprint(result)

    return offer

def add_cart_line_items(cart_retrieval_json, offer):
    # Will add the line items for each item (product-variant) in the proposal.
    for product_variant_index in range(0, len(offer['offer_list'])):
        line_items = cart_retrieval_json['data']['cartCreate']['cart']['lines']['edges']
        for line_item_index in range(0, len(line_items)):
            if line_items[line_item_index]['node']['merchandise']['id'] == offer['offer_list'][product_variant_index]['variants']['product_variant_id']:
                offer['offer_list'][product_variant_index]['variants']['line_item'] = line_items[line_item_index]['node']['id']


def get_country_code(country):
    # Will return the country code based on the country specified.
    # For now will assume that the country returned is correct.
    # Future versions will verify and return valid country codes based on country variable.
    return country

def remove_item_from_cart(offer):
    # Offer was rejected by the consumer or revoked by the supplier. Remove the item from cart.
    # Remove the line item from the cart.

    cart_id = offer['cart_id']
    line_item_to_delete = "["

    # Add all line items to a list for deletion.
    for line_item in offer['offer_list']:
        lineitem_id = line_item['variants']['line_item']
        line_item_to_delete = line_item_to_delete + f""" "{lineitem_id}", """

    line_item_to_delete = line_item_to_delete + "]"

    query_delete_item = f"""
        mutation {{
            cartLinesRemove(
                cartId: "{cart_id}",
                lineIds: {line_item_to_delete}
                ) {{
                    cart {{
                        id
                        createdAt
                        updatedAt
                        lines(first: 10) {{
                        edges {{
                            node {{
                            id
                            merchandise {{
                                ... on ProductVariant {{
                                id
                                }}
                            }}
                            }}
                        }}
                        }}
                        buyerIdentity {{
                        email,
                        phone,
                        deliveryAddressPreferences {{
                            __typename
                        }}
                        preferences {{
                            delivery {{
                            deliveryMethod
                            }}
                        }}
                        }}
                        attributes {{
                        key
                        value
                        }}
                        # The estimated total cost of all merchandise that the customer will pay at checkout.
                        cost {{
                        totalAmount {{
                            amount
                            currencyCode
                        }}
                        # The estimated amount, before taxes and discounts, for the customer to pay at checkout.
                        subtotalAmount {{
                            amount
                            currencyCode
                        }}
                        # The estimated tax amount for the customer to pay at checkout.
                        totalTaxAmount {{
                            amount
                            currencyCode
                        }}
                        # The estimated duty amount for the customer to pay at checkout.
                        totalDutyAmount {{
                            amount
                            currencyCode
                        }}
                        }}
                    }}
                    }}
                }}
        """

    payload = {'query': query_delete_item}
    result = requests.post(f"https://{config_shopify.myshop_name}.myshopify.com/api/{config_shopify.api_version}/graphql.json", headers=config_shopify.header_values, json=payload)
    result=json.loads(result.content)

    print('-----------------------------------------------\n\n')
    print('Delete item from cart\n')
    pprint(result)

    return True

def get_shopify_checkout_url(offer):
    # Will return the shopify URL to the checkout, so that the consumer agent's human owner can manually make the purchase.
    cart_id = offer['cart_id']
    query_checkout_url = f"""
        query checkoutURL {{
            cart(id: "{cart_id}") {{
            checkoutUrl
            }}
        }}
    """

    payload = {'query': query_checkout_url}
    result = requests.post(f"https://{config_shopify.myshop_name}.myshopify.com/api/{config_shopify.api_version}/graphql.json", headers=config_shopify.header_values, json=payload)
    result=json.loads(result.content)

    print('-----------------------------------------------\n\n')
    print('Cart Checkout URL\n')
    pprint(result)

    return result['data']['cart']['checkoutUrl']

def verify_order_created(agent_name, received_message, time_start_manual_purchase):
    # Will verify that the order was created for the consumer.
    # Will get orders from the email of the agent's owner, and search for any orders created in the last day.
    # Then will check if the order was created after the consumer started trhe process of manual purchase: time_start_manual_purchase.

    # https://shopify.dev/docs/api/admin-graphql/latest/queries/orders

    agent_owner_email = received_message.offer['consumer_details']['email']
    now = datetime.now()
    one_day = timedelta(days=1)
    now -= one_day
    time_minus_one_day = now.isoformat() + "Z"

    order_query=f"""
        query {{
        orders(first: 10, query: "email:{agent_owner_email} AND created_at:>'{time_minus_one_day}'", reverse:true, sortKey: CREATED_AT) {{
            edges {{
            node {{
                id
                name
                email
                confirmationNumber
                confirmed
                createdAt
                processedAt
                fullyPaid
                currencyCode
                statusPageUrl
                cancelledAt
                name
                displayFulfillmentStatus
                lineItems(first:200) {{
                edges {{
                    node {{
                    id
                    name
                    quantity
                    title
                    variant {{
                        id
                        price
                        title
                        displayName
                    }}
                    vendor
                    }}
                }}
                
                }}
                currentTotalPriceSet {{
                presentmentMoney {{
                    amount
                    currencyCode
                    }}
                    shopMoney {{
                    amount
                    currencyCode
                    }}
                }}
                currentTotalTaxSet{{
                presentmentMoney {{
                    amount
                    currencyCode
                    }}
                    shopMoney {{
                    amount
                    currencyCode
                    }}
                }}
            }}
            }}
        }}
        }}
    """

    payload = {'query': order_query}
    get_orders = requests.post(f"https://{config_shopify.myshop_name}.myshopify.com/admin/api/{config_shopify.api_version_admin}/graphql.json", headers=config_shopify.header_values_ADMIN, json=payload)
    result=json.loads(get_orders.content)

    print('-----------------------------------------------\n\n')
    print('Verify Order\n')
    pprint(result)

    # Now check if an order by the same customer (same email) has been created after time_start_manual_purchase. 
    for an_order in result['data']['orders']['edges']:
        order_created_at = an_order['node']['createdAt']
        time_order_created = datetime.strptime(order_created_at, "%Y-%m-%dT%H:%M:%S%z")

        if time_order_created > time_start_manual_purchase:
            if an_order['node']['fullyPaid']:
                # Order is fully paid, so return true.
                return True, 'Fully paid', an_order['node']['name'], an_order['node']
            else:
                # Order not paid. Assume error. Notify consumer agent.
                return False, 'Not fully paid', None
    
    # If gets here, order was not found.
    return False, 'Order not found', None

def process_payment_supplier(received_message, payment):
    # Process the payment for the order.
    # At the moment, Shopify requires manual purchase by a human vai their online store website.
    # Leave this for later when Shopify allows automated purchase via AI agents.
    pass

    # process_payment_response = 'credit card payment denied'
    process_payment_response = 'confirmed'
    return process_payment_response

def check_human_authorization(received_message, human_authorization):
    # Will check human authorization.
    # Since Shopify requires manual purchase by consumer agent owner, human authorization is implicit. So just return True.
    # Leave this for later when Shopify allows automated purchase via AI agents.
    return True

def complete_and_deliver_order(agent_name, order_message, order_name):
    # Wait until the order is fulfilled.
    # This will run in a thread. Future version will use Shopify web hooks so don't need to keep this thread running.
    
    # Check for fulfillment status each 3 hours until fulfilled.
    wait_for_next_check = 60*60*3

    while True:

        filfillment_status, canceled_at = get_order_filfillment_status(order_name)

        if filfillment_status == 'fulfilled':
            # Order is fulfilled. So let the consumer agent know.
            socontra.order_complete(agent_name, message_responding_to=order_message)
            break
        elif canceled_at is not None:
            # Looks like the order was canceled by the consumer. If the order was canceled by the Shop, then
            # would return the message below. However, unable to check who canceled, so just break and end the transaction.
            # socontra.cancel_order(agent_name, message='Sorry, had to cancel order. Will provide a refund', message_responding_to=order_message, recipient_type='consumer')
            break
        else:
            # Otherwise, wait 3 hours and check again.
            time.sleep(wait_for_next_check)

    # Wait for optional signoff from the consumer of the completed and delivered services.
    if filfillment_status == 'fulfilled' and order_delivery_signoff():
        # Wait for order complete confirmation.
        message_type, order_confirmation_returned = socontra.expect_multiple(agent_name, [order_complete_confirm_success, order_complete_confirm_fail])
        order_confirmation = order_confirmation_returned['received_message']

        if message_type == 'order_complete_confirm_success':
            # Perform any finalization or wrap up tasks and complete the transaction
            print('Customer confirmed order with message ', order_confirmation.message)
            pass
        else:
            # There was a problem with the completion/delivery of the order. Resolve issues here.
            print('Customer unhappy with order, message is ', order_confirmation.message, ' send a sorry card.')
            pass

    # End the dialogue for this process and return.
    socontra.close_dialogue(agent_name, order_message)


def get_order_filfillment_status(order_name):
    # Will return the filfillment status of the order.

    order_query=f"""
        query {{
            orders(first: 1, query: "name:'{order_name}'") {{
                edges {{
                    node {{
                        id
                        displayFulfillmentStatus
                        cancelledAt
                    }}
                }}
            }}
        }}
    """

    payload = {'query': order_query}
    get_orders = requests.post(f"https://{config_shopify.myshop_name}.myshopify.com/admin/api/{config_shopify.api_version_admin}/graphql.json", headers=config_shopify.header_values_ADMIN, json=payload)
    result=json.loads(get_orders.content)

    print('-----------------------------------------------\n\n')
    print('Check Order Fulfillment\n')
    pprint(result)

    filfillment_status = result['data']['orders']['edges'][0]['node']['displayFulfillmentStatus'].lower()
    canceled_at = result['data']['orders']['edges'][0]['node']['cancelledAt']
    return filfillment_status, canceled_at

def order_delivery_signoff():
    # Return True if the supplier requires signoff on the completion and delivery of the order.
    return True
