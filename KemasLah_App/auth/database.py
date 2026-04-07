import os
from datetime import datetime
from pymongo import MongoClient

MONGO_URI = "mongodb+srv://limzhihao0513_db_user:Ih9nx8rCN1700XUY@kemaslahcluster.815xmwv.mongodb.net/?appName=KemasLahCluster"


def get_formatted_size(path):
    """Calculates file size and formats it into KB, MB, or GB."""
    try:
        size = os.path.getsize(path)
        for unit in ["B", "KB", "MB", "GB", "TB"]:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} PB"
    except Exception:
        return "Unknown"


def share_file(file_path, owner_email, target_email, role, expiration_date):
    """Saves the file sharing permissions to MongoDB."""
    try:
        client = MongoClient(MONGO_URI)
        db = client["kemaslah_db"]

        db.shared_files.insert_one({
            "file_path": file_path,
            "owner_email": owner_email,
            "shared_with_email": target_email,
            "role": role,
            "expiration_date": expiration_date,
            "shared_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "file_size": get_formatted_size(file_path)
        })
        client.close()
        return True
    except Exception as e:
        print(f"MongoDB error while sharing: {e}")
        return False


def revoke_file_share(file_path, owner_email, target_email):
    """Removes a sharing record from MongoDB to revoke access."""
    try:
        client = MongoClient(MONGO_URI)
        db = client["kemaslah_db"]

        db.shared_files.delete_many({
            "file_path": file_path,
            "owner_email": owner_email,
            "shared_with_email": target_email
        })
        client.close()
        return True
    except Exception as e:
        print(f"MongoDB error while revoking share: {e}")
        return False


def update_file_share(file_path, owner_email, target_email, new_role, new_expiration):
    """Updates an existing file sharing record in MongoDB."""
    try:
        client = MongoClient(MONGO_URI)
        db = client["kemaslah_db"]

        db.shared_files.update_many(
            {
                "file_path": file_path,
                "owner_email": owner_email,
                "shared_with_email": target_email
            },
            {
                "$set": {
                    "role": new_role,
                    "expiration_date": new_expiration
                }
            }
        )
        client.close()
        return True
    except Exception as e:
        print(f"MongoDB error while updating share: {e}")
        return False


def request_extension(file_path, owner_email, target_email, requested_date):
    """Saves an extension request to MongoDB."""
    try:
        client = MongoClient(MONGO_URI)
        db = client["kemaslah_db"]

        db.shared_files.update_one(
            {
                "file_path": file_path,
                "owner_email": owner_email,
                "shared_with_email": target_email
            },
            {
                "$set": {
                    "extension_status": "Pending",
                    "requested_date": requested_date
                }
            }
        )
        client.close()
        return True
    except Exception as e:
        print(f"MongoDB error while requesting extension: {e}")
        return False


def resolve_extension(file_path, owner_email, target_email, new_expiry, status):
    """Approves or rejects an extension request."""
    try:
        client = MongoClient(MONGO_URI)
        db = client["kemaslah_db"]

        update_data = {"extension_status": status}
        if status == "Approved" and new_expiry:
            update_data["expiration_date"] = new_expiry

        db.shared_files.update_one(
            {
                "file_path": file_path,
                "owner_email": owner_email,
                "shared_with_email": target_email
            },
            {
                "$set": update_data
            }
        )
        client.close()
        return True
    except Exception as e:
        print(f"MongoDB error while resolving extension: {e}")
        return False