//code adapted from: https://dev.to/ara225/how-to-use-bootstrap-modals-without-jquery-3475

function openModal(modal_id) {
    document.getElementById("backdrop").style.display = "block"
    document.getElementById(modal_id).style.display = "block"
    document.getElementById(modal_id).classList.add("show")
}

function closeModal(modal_id) {
    document.getElementById("backdrop").style.display = "none"
    document.getElementById(modal_id).style.display = "none"
    document.getElementById(modal_id).classList.remove("show")
}

function addModalData(modal_id, _content_type_id, _object_id) {
    const form = document.getElementById(modal_id).querySelector(`#${modal_id} form`)

    form.querySelector('[id*="_content_type"]').value = _content_type_id

    form.querySelector('[id*="_object_id"]').value = _object_id
}
