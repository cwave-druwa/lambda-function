import boto3
import os

s3 = boto3.client('s3')
ecr_client = boto3.client('ecr')
ecs_client = boto3.client('ecs')

BUCKET_NAME = "ecs-image-digest-bucket"
OBJECT_KEY = "previous_image_digest.txt"

# ECR 설정
account_id = "381492005553"
region = "ap-south-1"
repository_name = "olive-young-server-dr"
tag = "latest-dr"

# ECR 이미지 URI 구성
image_uri = f"{account_id}.dkr.ecr.{region}.amazonaws.com/{repository_name}:{tag}"

def lambda_handler(event, context):
    try:
        print(f"시도중 ...")
        repository_name = "olive-young-server-dr"
        tag = "latest-dr"
        
        # ECR에서 최신 이미지 조회
        response = ecr_client.describe_images(repositoryName=repository_name, imageIds=[{'imageTag': tag}])
        latest_digest = response['imageDetails'][0]['imageDigest']
        
        # S3에서 이전 다이제스트 값 읽기
        try:
            previous_digest_object = s3.get_object(Bucket=BUCKET_NAME, Key=OBJECT_KEY)
            previous_digest = previous_digest_object['Body'].read().decode('utf-8').strip()
            previous_message = f"Previous digest from S3: {previous_digest}"  # 이전 다이제스트 값 출력
        except s3.exceptions.NoSuchKey:
            previous_digest = ""
            previous_message = "No previous digest found in S3, setting to empty string."
        

        latest_message = f"Latest digest from ECR: {latest_digest}"  # 최신 다이제스트 값 출력


        # 이미지가 변경되었는지 확인
        if latest_digest != previous_digest:

            # S3에 새로운 다이제스트 값 저장
            s3.put_object(Bucket=BUCKET_NAME, Key=OBJECT_KEY, Body=latest_digest)
            
            # ECS 서비스 업데이트를 트리거하여 새로운 태스크 정의 사용
            #update_response = ecs_client.update_service(
            #    cluster='prod-ecs-cluster-mb',
            #    service='olive-service',
            #    forceNewDeployment=True
            #)
            #update_message = f"ECS 서비스 업데이트 완료: {update_response}"

            # 새로운 태스크 정의를 등록
            task_def_response = ecs_client.register_task_definition(
                family='olive-task',
                containerDefinitions=[
                    {
                        'name': 'olive',
                        'image': image_uri,  # 최신 이미지 사용
                        'cpu': 512,
                        'memory': 1024,
                        'essential': True,
                        'portMappings': [
                            {
                                'containerPort': 8080,
                                'hostPort': 8080
                            }
                        ]
                    }
                ],
                requiresCompatibilities=['FARGATE'],
                networkMode='awsvpc',
                memory='1024',
                cpu='512',
                executionRoleArn='arn:aws:iam::381492005553:role/lambda_exec_role'  # 실행 역할 ARN
            )
            
            # 새로운 태스크 정의 ARN 가져오기
            new_task_definition = task_def_response['taskDefinition']['taskDefinitionArn']
            
            # ECS 서비스 업데이트를 트리거하여 새로운 태스크 정의 사용
            update_response = ecs_client.update_service(
                cluster='prod-ecs-cluster-mb',
                service='olive-service',
                taskDefinition=new_task_definition,  # 새로 등록된 태스크 정의 사용
                forceNewDeployment=True
            )
            update_message = f"ECS 서비스 업데이트 완료: {update_response}"
        else:
            update_message = "이미지가 최신 상태입니다."
    
    except Exception as e:
        error_message = f"오류 발생: {str(e)}"
        return {
            'statusCode': 500,
            'body': error_message
        }

    # 결과 반환
    return {
        'statusCode': 200,
        'body': {
            'previous_digest_message': previous_message,
            'latest_digest_message': latest_message,
            'update_message': update_message
        }
    }
