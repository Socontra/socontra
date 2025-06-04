# SET UP VARIABLES TO ACCESS THE SHOPIFY STORE.
# Refer files: socontra_shopify_web_agent.py and socontra_transact_shopify_protocol_supplier.py

# Add Shopify shop name.
myshop_name='<myshop_name>'       # This will also be the agent name. This is from the store url: https://<myshop_name>.myshopify.com/

# Credentials for Shopify Storefront API which searches for products, add products to cart, and returns a URL to the human user
# to manually make a purchase.
# To get the access token: 
#   When you log in to your store, go to 'Settings' (lower left corner) -> 'Apps and sales channels' -> 'Develop apps' (top right).
#   If app not created: 
#           Create an app for the store by clicking on the 'Create an app' button. Enter app name and developer, and click 'Create app'.
#           Click on the 'API credentials' tab at the top of the page, and click 'Configure Storefront API scopes'
#           Go through process of selecting access permissions. Once created, you should see the access token 
#           when you click on the 'API credentials' tab at the top of the page.
API_ACCESS_TOKEN_STOREFRONT='<Storefront API access token here>'    # Storefront API Access Token
api_version = '2025-04'

# Credentials for Shopify Admin API to check for created orders and order fulfillment.
# Similar process to get the API_TOKEN_ADMIN as with Storefront API API_ACCESS_TOKEN_STOREFRONT above.
#           after you 'Configure Admin API scopes', click on the 'API Credentials' at the top of the screen.
#           Click 'Install app', then Install.
API_TOKEN_ADMIN='<Admin API access token here>'
api_version_admin = '2025-01'

# Business categories (groups) and geographical regions
# See demo 6, 7 (part 1 to 3) and 8 for more info on groups and regions.
# Join public 'socontra' groups that represent the online store's business categories for types of products that the store sells.
# For each business category (group), add geographical region(s) that the store services.
# The taxonomy for socontra standard business categories can be viewed in file: data/socontra_public_groups.json, which is the  
# comprehensive list from Yelp (https://docs.developer.yelp.com/docs/resources-categories). Consistency with Yelp can help the  
# consumer agent or agent owner utilize Yelp to confirm your store's credibility.
# You can also create your own public groups (open or restricted).
# Geographical regions are specified using 'country', 'state', and 'city', which must utilize names in the file 
# data/countries+states+cities.json which is from https://github.com/dr5hn/countries-states-cities-database/tree/master.
# Example is:
business_categories_and_regions = [
    {'group': ['socontra', 'Restaurants', 'Australian'],    # Web Agent online store sells/delivers Australian food.
     'regions': [
                    {'country': 'US'},   # Service a whole country
                    {'country': 'US', 'state': 'CA'},   # Service a state
                    {'country': 'US', 'state': 'CA', 'city': 'Los Angeles'},   # Service a local region/city.
                ]
     },
     {'group': ['socontra', 'Restaurants', 'Italian', 'Abruzzese'],    # Web Agent online store sells/delivers Italian-Abruzzese food.
     'regions': [
                    {'country': 'US'},   # Service a whole country
                    {'country': 'US', 'state': 'NY'},   # Service a state
                    {'country': 'US', 'state': 'NY', 'city': 'New York City'},   # Service a local region/city.
                ]
     },
]

# Create variables used by the Shopify agent.
shop_url = f'https://{myshop_name}.myshopify.com'

header_values = {"X-Shopify-Storefront-Access-Token": API_ACCESS_TOKEN_STOREFRONT,
                  "Content-Type": "application/json"}

header_values_ADMIN = {"X-Shopify-Access-Token": API_TOKEN_ADMIN,
                  "Content-Type": "application/json"}
