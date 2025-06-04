# Socontra Shopify Web Agent Template
# Uses the Socontra 'transact' protocol, suited for automated commercial transactions by Web Agents.
# Web Agents are online store replicates designed specifically to service other agents/bots.

# Refer files:
# - config_shopify.py
# - protocol_templates/online_stores/socontra_transact_shopify_protocol_supplier.py

# Also see the overview and tutorial on the socontra.com web site, comments in socontra_demo_9.py file,
# and the 'transact' protocol diagram in file Socontra service protocols.pdf.

from socontra.socontra import Socontra
from protocol_templates import  socontra_main_protocol
from protocol_templates.online_stores import  socontra_transact_shopify_protocol_supplier
import config, config_shopify

socontra = Socontra()
socontra.add_protocol(socontra_main_protocol)
socontra.add_protocol(socontra_transact_shopify_protocol_supplier)

if __name__ == '__main__':

    # Enter your agent credentials in the config.py file.
    client_public_id = config.client_public_id
    client_security_token = config.client_security_token

    shopify_agent = client_public_id + ':' + 'shopify_' + config_shopify.myshop_name

    # Connect (and register if not already) the agent to the Socontra Network, to allow it to message, interact and transact with other agents.
    # Credentials for each new agent to connect back to the Socontra Network are stored in folder socontra/database.
    socontra.connect_socontra_agent(agent_data={
            'agent_name': shopify_agent,
            'client_security_token': client_security_token,
            'human_password': 'human_password_for_agent_here',
        }, clear_backlog = True)

    # Join the public groups relating to the Web Agent online store's business category,
    # and add the geographical regions that the store services.
    # The list of busines scategories (groups) and regions are specified in file 'config_shopify.py'
    for single_business_category_and_regions in config_shopify.business_categories_and_regions:
        socontra.join_group(shopify_agent, single_business_category_and_regions['group'])
        socontra.add_region_group(shopify_agent, single_business_category_and_regions['group'], single_business_category_and_regions['regions'])

    # Wait for agent task/product requests to be received - via transaction endpoints in file
    # protocol_templates/online_stores/socontra_transact_shopify_protocol_supplier.py.

    # Remember to delete_region_group() and unjoin() the public groups if testing. Delete regions first, then the group.
    # for single_business_category_and_regions in config_shopify.business_categories_and_regions:
    #     socontra.delete_region_group(shopify_agent, single_business_category_and_regions['group'], single_business_category_and_regions['regions'])
    #     socontra.unjoin_group(shopify_agent, single_business_category_and_regions['group'])
        