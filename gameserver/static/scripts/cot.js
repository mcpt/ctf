const fields = document.getElementsByClassName("cotangent");
for (let field in fields) {
  resultField.innerHTML = await cotangent(field.innerText);
}
