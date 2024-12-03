#!/bin/bash

# Define file paths
FILE1="/home/satyam-hacker/Pictures/Screenshots/q12.png"
FILE2="/home/satyam-hacker/Pictures/Screenshots/q11.png"

# Encode files to base64
base64 "$FILE1" > q12_base64.txt
base64 "$FILE2" > q11_base64.txt

# Create JSON payload
cat > payload.json << EOF
{
    "subject": "Screenshots Attached",
    "body": "Please find the attached screenshots",
    "recipients": ["220010053@iitdh.ac.in","220110008@iitdh.ac.in"],
    "embedded_links": ["https://google.com"],
         "cc": ["gamermg474@gmail.com"],
         "bcc": ["220110014@iitdh.ac.in"],
    "attachments": [
        {
            "filename": "q12.png",
            "content": "$(cat q12_base64.txt)",
            "mime_type": "image/png"
        },
        {
            "filename": "q11.png",
            "content": "$(cat q11_base64.txt)",
            "mime_type": "image/png"
        }
    ]
}
EOF

# Send email using curl
curl -X POST http://localhost:8000/send-email/ \
     -H "Content-Type: application/json" \
     -d @payload.json

# Cleanup temporary files
rm q12_base64.txt q11_base64.txt payload.json
