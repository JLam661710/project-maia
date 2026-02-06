curl https://ark.cn-beijing.volces.com/api/v3/responses \
-H "Authorization: Bearer 285deffd-697c-4ae4-97ad-2b1d0847688f" \
-H 'Content-Type: application/json' \
-d '{
    "model": "doubao-seed-1-8-251228",
    "input": [
        {
            "role": "user",
            "content": [
                {
                    "type": "input_image",
                    "image_url": "https://ark-project.tos-cn-beijing.volces.com/doc_image/ark_demo_img_1.png"
                },
                {
                    "type": "input_text",
                    "text": "你看见了什么？"
                }
            ]
        }
    ]
}'