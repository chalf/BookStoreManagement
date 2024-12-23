import cloudinary.uploader


# Lấy public_id từ url ảnh trên cloudinary
def get_public_id(secure_url):
    return secure_url.split('/')[-1].split('.')[0]


# Xóa ảnh trên cloudinary
def delete_img(public_id):
    response = cloudinary.uploader.destroy(public_id)
    if response['result'] == 'ok':
        print(f"Image with public_id '{public_id}' deleted successfully.")
    else:
        print(f"Failed to delete image: {response['result']}")
