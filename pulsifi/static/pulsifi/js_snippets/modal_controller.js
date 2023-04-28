//code adapted from: https://dev.to/ara225/how-to-use-bootstrap-modals-without-jquery-3475

function openModal(modal_id) {
    const modal = document.getElementById(modal_id)

    document.getElementById("backdrop").style.display = "block"
    modal.style.display = "block"
    modal.classList.add("show")
}

function closeModal(modal_id) {
    const modal = document.getElementById(modal_id)
    if (modal_id === "create-reply-modal") {
        modal.querySelector(`#${modal_id} form`).querySelector('[id*="message"]').value = ""
    } else if (modal_id === "create-report-modal") {
        const form = modal.querySelector(`#${modal_id} form`)
        form.querySelector('[id*="reason"]').value = ""
        form.querySelector('[id*="category"]').selectedIndex = 0
    }
    document.getElementById("backdrop").style.display = "none"
    modal.style.display = "none"
    modal.classList.remove("show")
}

function addModalData(modal_id, _content_type_id, _object_id) {
    const form = document.getElementById(modal_id).querySelector(`#${modal_id} form`)

    form.querySelector('[id*="_content_type"]').value = _content_type_id

    form.querySelector('[id*="_object_id"]').value = _object_id
}
