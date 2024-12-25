function changeUserAvatar(){
    const file = event.target.files[0];
    /*event là sự kiện vừa xảy ra của element mà nó gắn, trường hợp này là onchange
    event.target trả về đối tượng Element mà nó gắn, trường hợp này là <input>
    Trong thẻ input type=file có thuộc tính files chứa các file được tải lên
    */
    if (!file)
        return;
    // Tạo đối tượng FormData để gửi file
    const formData = new FormData(); // kiểu form-data của request body
    // Thêm file vào FormData với key là 'avatar'
    formData.append('avatar', file);
    // Gửi request POST đến server
    fetch('/api/user/edit/', {
        method: 'POST',
        body: formData  // Sử dụng FormData làm body của request
        // Không cần chỉ định Content-Type vì FormData gán cho body là nó tự hiểu
    }).then(response => response.ok)
    .then(status => {
        if (status === true)
            window.location.reload()
    })
    window.alert('Vui lòng đợi trong vài giây để cập nhật avatar');
}