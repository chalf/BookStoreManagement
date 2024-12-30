const myModal = document.getElementById('myModal');
myModal.addEventListener('shown.bs.modal', function () {
    setTimeout(() => {
        const modal = bootstrap.Modal.getInstance(myModal);
        modal.hide();
    }, 1000);
});
