import os


class DevelopmentConfig:
    user_pool_id = 'us-west-2_ViB3UFcvp'
    app_id = '2g2eg0g7tbjhbaa45diohmvqhs'
    rest_endpoint = 'https://v8p9pmg3hb.execute-api.us-west-2.amazonaws.com/dev'
    data_endpoint = 'https://drdt2z4kljdbte5s4zx623kyk4.appsync-api.us-west-2.amazonaws.com/graphql'


class ProductionConfig:
    user_pool_id = 'us-west-2_LQnstneoZ'
    app_id = '7ic2n55r9h4fj0qej5q9ikr2o1'
    rest_endpoint = 'https://2yi247yljl.execute-api.us-west-2.amazonaws.com/prd'
    data_endpoint = 'https://22boctowkfbuzaidvbvwjxfnai.appsync-api.us-west-2.amazonaws.com/graphql'


if os.environ.get('ENV', '').upper() == 'DEV':
    config = DevelopmentConfig()
else:
    config = ProductionConfig()
