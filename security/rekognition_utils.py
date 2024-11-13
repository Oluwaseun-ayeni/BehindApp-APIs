import boto3
from botocore.exceptions import ClientError

# Create a Rekognition client using AWS credentials
rekognition_client = boto3.client('rekognition')

def compare_faces(source_image_bytes, target_image_bytes):
    """
    Compare two faces using Amazon Rekognition's compare_faces API.
    Returns a dictionary with the match status and similarity score.
    """
    try:
        # Call Rekognition API to compare faces
        response = rekognition_client.compare_faces(
            SourceImage={
                'Bytes': source_image_bytes
            },
            TargetImage={
                'Bytes': target_image_bytes
            },
            SimilarityThreshold=90  # Adjust the similarity threshold as needed
        )

        # Check if faces match and return the result
        if response['FaceMatches']:
            return {
                'valid': True,
                'confidence': response['FaceMatches'][0]['Similarity']  # Match confidence
            }
        else:
            return {'valid': False, 'confidence': 0}
    
    except ClientError as e:
        return {'error': str(e)}
