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

function addToCart(id, name, price, image){
    console.log(image);
    fetch('/api/carts/', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
            id: id,
            title: name,
            price: price,
            image: image
        })
    })
}

function updateCartSummary(data) {
    let amounts = document.getElementsByClassName("cart-amount");
    for (let item of amounts){
        item.innerHTML = data.total_amount.toLocaleString() + " đ";
    }
    amounts = document.getElementsByClassName("cart-counter");
    for (let item of amounts){
        item.innerHTML = data.total_quantity;
    }
}

function updateCart(bookId, obj) {
    fetch(`/api/carts/${bookId}`, {
        method: "put",
        body: JSON.stringify({
            "quantity": obj.value
        }),
        headers: {
            "Content-Type": "application/json"
        }
    }).then(res => res.json()).then(data => {
        updateCartSummary(data);
    })
}

function deleteCart(bookId) {
    if (confirm("Bạn chắc chắn xóa không?") === true) {
        fetch(`/api/carts/${bookId}`, {
            method: "delete"
        }).then(res => res.json()).then(data => {
            updateCartSummary(data);
            document.getElementById(`cart${bookId}`).style.display = "none";
        });
    }
}
