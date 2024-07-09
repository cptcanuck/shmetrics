import boto3
import json


def get_cloudformation_outputs(stack_name):
    # Create a CloudFormation client
    cf_client = boto3.client("cloudformation")

    try:
        # Get the stack outputs
        response = cf_client.describe_stacks(StackName=stack_name)
        stack_outputs = response["Stacks"][0]["Outputs"]

        # Create a dictionary to store the output values
        output_values = {}
        output_descriptin_values = {}
        print("Getting outputs from CFN stack: ", stack_name)
        # Extract the output key-value pairs
        for output in stack_outputs:
            output_key = output["OutputKey"]
            output_value = output["OutputValue"]
            output_description = output["Description"]
            output_values[output_key] = output_value
            output_descriptin_values[output_key] = output_description
            print(
                "Output Key: ",
                output_key,
                " Output Value: ",
                output_value,
                " Output Description: ",
                output_description,
            )

        return output_values, output_descriptin_values

    except Exception as e:
        print(f"Error getting CloudFormation stack outputs: {str(e)}")
        return None


def write_outputs_to_json(outputs, output_descriptions):
    # Create a dictionary to store the insights
    insights = []
    # Iterate over the output values
    for key, value in outputs.items():
        # Create an insight dictionary
        insight = {
            "id": key,
            "name": output_descriptions[key],
            "disabled": False,
            "arn": value,
        }
        # Append the insight to the insights list
        insights.append(insight)
        print("Wrote insight ", output_descriptions[key])
    # Create a dictionary with the insights list
    insights_dict = {"insights": insights}
    # Write the insights to a JSON file
    with open("cfnv2sechub/insights.json", "w") as file:
        json.dump(insights_dict, file, indent=4)


stack_name = "SH-Insights"
print("Getting outputs for stack: ", stack_name)

# Get the CloudFormation stack outputs
outputs, output_descriptions = get_cloudformation_outputs(stack_name)

if outputs:
    # Write the output values to a file
    write_outputs_to_json(outputs, output_descriptions)

else:
    print("Failed to get CloudFormation stack outputs")
