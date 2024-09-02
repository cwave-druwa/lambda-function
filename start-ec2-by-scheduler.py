## 담당자 유재균

import boto3

# 리전 설정
region = 'ap-northeast-2'

# EC2 클라이언트 초기화
ec2 = boto3.client('ec2', region_name=region)

def lambda_handler(event, context):
    # 중지된 모든 인스턴스의 ID를 가져오기
    response = ec2.describe_instances(
        Filters=[
            {'Name': 'instance-state-name', 'Values': ['stopped']}
        ]
    )
    
    # 중지된 인스턴스 ID 추출
    instances = []
    for reservation in response['Reservations']:
        for instance in reservation['Instances']:
            instances.append(instance['InstanceId'])
    
    # 중지된 인스턴스가 있으면 시작
    if instances:
        start_response = ec2.start_instances(InstanceIds=instances)
        print(f'Started instances: {instances}')
        print('Response:', start_response)
        return {
            'statusCode': 200,
            'body': f'Successfully started instances: {instances}'
        }
    else:
        print('No stopped instances found.')
        return {
            'statusCode': 200,
            'body': 'No stopped instances to start.'
        }
