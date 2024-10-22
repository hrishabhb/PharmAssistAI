import json
import boto3

def lambda_handler(event, context):
    # Create a Bedrock Runtime client
    client = boto3.client('bedrock-runtime', region_name='us-west-2')
    
    # Set the model ID for Llama 3.1 8B
    model_id = "meta.llama3-1-70b-instruct-v1:0"
    
    # Extract parameters from the event input
    # Parse the JSON body
    body = json.loads(event['body'])
    prompt = body.get("prompt", "give me something about cats")
    
    # Prepare the request body with only supported parameters
    request_body = {
        "prompt": f"<|begin_of_text|><|start_header_id|>user<|end_header_id|> {prompt} <|eot_id|> <|start_header_id|>assistant<|end_header_id|>"
    }
    
    try:
        # Invoke the model with modelId as a parameter and body as JSON
        response = client.invoke_model(
            modelId=model_id,
            body=json.dumps(request_body),
            contentType='application/json',
            accept='application/json'
        )
        
        # Decode and return the response
        response_body = json.loads(response['body'].read().decode('utf-8'))
        generated_text = response_body.get("generation", "")
        
        return {
            'statusCode': 200,
            'body': json.dumps({"response": generated_text})
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({"error": f"Error invoking model: {str(e)}"})
        }
