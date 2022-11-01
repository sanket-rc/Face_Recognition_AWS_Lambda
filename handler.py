import boto3
import face_recognition
import os, urllib.parse
import pickle

input_bucket = "mylambdainputproject"
output_bucket = "mylambdaoutputproj2"
table_name = "myfirstdb"

# Function to read the 'encoding' file
def open_encoding(filename):
	file = open(filename, "rb")
	data = pickle.load(file)
	file.close()
	return data

def download_Video(image_path, image_name):
    s3_client = boto3.client('s3')
    s3_client.download_file(input_bucket, image_name, image_path)

def face_recognition_handler(event, context):
	print("Python is called")
	vfile_name = urllib.parse.unquote_plus(event['Records'][0]['s3']['object']['key'], encoding='utf-8')
	print(vfile_name)
	
	image_download_path = "/tmp/{0}".format(vfile_name)
	download_Video(image_download_path, vfile_name)
	print("Image downloaded successfully")
	image_file_name = vfile_name.split(".")[0]
	os.system("ffmpeg -i " + str(image_download_path) + " -r 1 " + str("/tmp/") + image_file_name + ".jpeg")
	
	
	results = getResults(image_file_name)
	print(results)

	uploadToOutputBucket(image_file_name,results)
	print("Upload to S3 successful")
	return


def getResults(file_name):
	image_download_path = "/tmp/{0}.jpeg".format(file_name)
	loaded_image = face_recognition.load_image_file(image_download_path)
	encoded_image = face_recognition.face_encodings(loaded_image)[0]
	encoding_file = os.path.basename("encoding")
	encoded_file_data = open_encoding(encoding_file)
	file_encodings = encoded_file_data['encoding']
	length = len(file_encodings)
	for idx in range(length):
		if face_recognition.compare_faces([encoded_image], file_encodings[idx])[0]:
			print(encoded_file_data['name'][idx])
			return encoded_file_data['name'][idx]

def uploadToOutputBucket(file_name, face_recognition_results):
	s3_client = boto3.client('s3')
	dynamodb = boto3.client('dynamodb')
	response = dynamodb.get_item(
		TableName = table_name,
		Key={
			'name': {'S': face_recognition_results}
		})
	print(response)
	resp_body = "{0},{1},{2}".format(face_recognition_results, response['Item']['major']['S'], response['Item']['year']['S'])
	output_file_name = file_name + ".csv"
	s3_client.put_object(Key=output_file_name,Bucket= output_bucket,Body=resp_body)
