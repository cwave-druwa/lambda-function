## 담당자 유재균

import boto3

# 리전 설정
region = 'ap-northeast-2'

# EC2 클라이언트 초기화
ec2 = boto3.client('ec2', region_name=region)

def lambda_handler(event, context):
    # 실행 중인 모든 인스턴스의 ID를 가져오기
    response = ec2.describe_instances(
        Filters=[
            {'Name': 'instance-state-name', 'Values': ['running']}
        ]
    )

    # 실행 중인 인스턴스 ID 추출
    instances = []
    for reservation in response['Reservations']:
        for instance in reservation['Instances']:
            instances.append(instance['InstanceId'])

    # 실행 중인 인스턴스가 있으면 중지
    if instances:
        stop_response = ec2.stop_instances(InstanceIds=instances)
        print(f'Stopped instances: {instances}')
        print('Response:', stop_response)
        return {
            'statusCode': 200,
            'body': f'Successfully stopped instances: {instances}'
        }
    else:
        print('No running instances found.')
        return {
            'statusCode': 200,
            'body': 'No running instances to stop.'
        }
