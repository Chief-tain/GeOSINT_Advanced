def change_data_format(dataset):
    
    converted_dataset = []
    dataset = [el[0] for el in dataset]
            
    for row in dataset:
        converted_dataset.append(
            {
            "MESSAGE_ID": row.message_id,
            "SENDER": row.sender,
            "CHAT_TITLE": row.chat_title,
            "DATE": row.date,
            "TEXT": row.text,
            "TOKENS": row.tokens,
            "EMBEDDINGS": row.embedding
            }
            )
        
    return converted_dataset