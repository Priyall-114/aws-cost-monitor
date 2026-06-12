import json
import boto3
from datetime import datetime
from decimal import Decimal

dynamodb=boto3.resource('dynamodb')
sns=boto3.client('sns')
budgets=boto3.client('budgets',region_name='us-east-1')
ce = boto3.client('ce', region_name='us-east-1')
resource_explorer=boto3.client('resource-explorer-2', region_name='ap-south-1')
s3=boto3.client('s3')

Table_name='aws-daily-costs'
SNS_topic_arn='arn:aws:sns:ap-south-1:849808308190:aws-cost-alerts'
budget_name='My Monthly Cost Budget'
account_id='849808308190'


def lambda_handler(event, context):
    response=budgets.describe_budget(AccountId=account_id,BudgetName=budget_name)
    budget=response['Budget']
    limit=float(budget['BudgetLimit']['Amount'])
    actual=float(budget['CalculatedSpend']['ActualSpend']['Amount'])

    #service wise fetching data
    today=datetime.today()
    start=today.strftime('%Y-%m-01')
    end=today.strftime('%Y-%m-%d')#Today's date ins tring format coz the method below wants in string
    ce_response=ce.get_cost_and_usage(
        TimePeriod={'Start':start, 'End':end},#Kab s kab tak ka data chaiye (month k day one say today tak ka)
        Granularity='MONTHLY',#How i want the data like monthly tou month k hisab s jo data aayega wo divided hoga aur daily hota tou it would have been like 1 june 2 jubne and so on so this is meant
        #Metrics-What information do you want AWS to return? Think of asking a teacher:Tell me my:- Marks - Attendance - Rank  These are different metrics.
        #fow aws cost metrics can be unbelnedecost,blended,amortized etc etc
        Metrics=['UnblendedCost'],#Return actual spending amount.
        #Now we need to group obtained data based on service
        GroupBy=[{'Type':'DIMENSION', 'Key':'SERVICE'}]#Group data by service name
    )
    service_costs={}
    for result in ce_response['ResultsByTime'][0]['Groups']:
        service_name = result['Keys'][0]
        cost = result['Metrics']['UnblendedCost']['Amount']
        service_costs[service_name] = str(cost)
    
    resource_response=resource_explorer.search(QueryString='*',MaxResults=100)
    #print(resource_response['Resources'][0])
    USEFUL_TYPES = {
    'lambda:function',
    's3:bucket', 
    'dynamodb:table',
    'elasticbeanstalk:environment',
    'ec2:instance',
    'sns:topic',
    'iam:role',
    'rds:db',
    'rds:cluster',
    'eks:cluster',
    'ecs:cluster',
    'ecs:service',
    'apigateway:restapi',
    'apigateway:apis',
    'cloudfront:distribution',
    'sqs:queue',
    'kinesis:stream',
    'elasticache:cluster',
    'opensearch:domain',
    'secretsmanager:secret',
    'cognito-idp:userpool'
    }

    active_resources={}
    for resource in resource_response['Resources']:
        resource_type=resource['ResourceType']  # jaise "aws:lambda:function"
        #short_type = resource_type.split(':',1)[1]  # "aws:" hata ke "lambda:function" b
    
        if resource_type not in USEFUL_TYPES:  # agar useful nahi toh skip karo
            continue
    
        resource_arn=resource['Arn']
        #resource_name=resource_arn.split(':')[-1]
    
        if resource_type not in active_resources:
            active_resources[resource_type]={
             'count':0,
                'resources':[]
            }
        active_resources[resource_type]['count']+=1
        active_resources[resource_type]['resources'].append(resource_type)

    #Saving data to Dynamodb    
    table=dynamodb.Table(Table_name)
    table.put_item(Item={
    'date':datetime.today().strftime('%Y-%m-%d'),
    'Spend-Amount':str(actual),
    'budget-limit':str(limit),
    'budget_remaining':Decimal(str(limit-actual)),
    'service_breakdown': service_costs ,
    'active_resources':json.dumps(active_resources)#(Saved as string)active_resources ek nested dict hai — DynamoDB nested dicts directly store kar leta hai but resources andar list hai, toh safe rehne ke liye json.dumps se string bana dete hain. 
    })

    #Reading data from dynamodb
    history_response=table.scan()#gives json and additional metadata as well
    history_items=history_response['Items']#actual data is in this only
    history_data=[]
    for item in history_items:
        history_data.append({
            'date':item['date'],
            'spend_amount':float(item['Spend-Amount']),
            'budget_limit':float(item['budget-limit']),
            'budget_remaining':float(item['budget_remaining']),
            'service_breakdown':item['service_breakdown'],
            'active_resources':json.loads(item['active_resources'])#it was string so converting it to python object

        })


    #Sorting data date wise
    history_data.sort(key=lambda x: x['date'])

    #Saving on s3 now as history_data
    s3.put_object(
     Bucket='cost-monitor-dashboard-priyal', 
     Key='history.json',
     Body=json.dumps(history_data),
     ContentType='application/json'
        )

    dashboard_data={
    'date':datetime.today().strftime('%Y-%m-%d'),
    'actual_spend':actual,
    'limit':limit,
    'budget_remaining': float(limit-actual),
    'service_breakdown': service_costs,
    'active_resources': active_resources #DICT
    }

    s3.put_object(Bucket='cost-monitor-dashboard-priyal', Key='dashboard_data.json', Body=json.dumps(dashboard_data),ContentType='application/json')

    #Checking if limit excceded first by 50 per then 80 then exhausted
    if actual/limit >= 0.5 and actual/limit < 0.8:
       sns.publish(TopicArn=SNS_topic_arn,
                Message='You have used 50% of your budget! \n Spend Amount='+str(actual)+'\n Budget='+str(limit)+'\n Remaining Budget='+str(limit-actual),
                Subject='AWS COST ALERT: 50% threshold reached!')
    elif actual/limit >= 0.8 and actual/limit < 1:
        sns.publish(TopicArn=SNS_topic_arn,
                Message='You have used 80% of your budget! \n Spend Amount='+str(actual)+'\n Budget='+str(limit)+'\n Remaining Budget='+str(limit-actual),
                Subject='AWS COST ALERT: 80% threshold reached!')
    elif actual/limit >= 1:
        sns.publish(TopicArn=SNS_topic_arn,
                Message='You have used 100% of your budget! \n Spend Amount='+str(actual)+'\n Budget='+str(limit)+'\n Remaining Budget='+str(limit-actual),
                Subject='AWS COST ALERT: Total Budget Assigned By you is finished, Add more Budget!')
    return {'statusCode': 200, 'body': json.dumps({'actual': actual, 'limit': limit,'budget_remaining':limit-actual})}