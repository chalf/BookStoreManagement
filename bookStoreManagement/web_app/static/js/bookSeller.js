function updateUI(data){
    if (data != 0){
        const node = document.getElementById('total').lastChild;
        node.firstChild.nodeValue = data.total_amount.toLocaleString();
    }

}

function deleteOrder(bookId) {
    if (confirm("Bạn chắc chắn xóa không?") === true) {
        fetch(`/api/sale-book/${bookId}`, {
            method: "delete"
        }).then(res => res.json()).then(data => {
            updateUI(data);
            document.getElementById(`order${bookId}`).style.display = "none";
        });
    }
}


function addOrder(id, isbn, name, price){
    fetch('/api/sale-book', {
        method: "post",
        body: JSON.stringify({
            "id": id,
            "isbn": isbn,
            "name": name,
            "price": price
        }),
        headers: {
            'Content-Type': 'application/json'
        }
    }).then(res => res.json()).then(data => {
        const orderTable = document.getElementById('orderList').querySelector('tbody');
        let newRow = document.createElement('tr');
        newRow.id = "order${id}"
        newRow.innerHTML = `
            <td>${isbn}</td>
            <td>${name}</td>
            <td><input type="number" class="form-control quantity" value="1" min="1" onblur="updateOrder(${ id }, this)"></td>
            <td>${price.toLocaleString()}</td>
            <td>
                <button class="btn btn-danger btn-sm" onclick="deleteOrder(${id})">&times;</button>
            </td>
        `;
        orderTable.appendChild(newRow);

        updateUI(data);
    })
}

function updateOrder(bookId, obj) {
    fetch(`/api/sale-book/${bookId}`, {
        method: "put",
        body: JSON.stringify({
            "quantity": obj.value
        }),
        headers: {
            "Content-Type": "application/json"
        }
    }).then(res => res.json()).then(data => {
        updateUI(data);
    })
}

function createOrderToSerVer(){
    fetch('/api/orders', {
        method: "post",
    }).then(res => res.json()).then(data => {
        if (data.status === 201){
            alert('Đơn hàng được tạo thành công');
            location.reload();
        }
    })
}
