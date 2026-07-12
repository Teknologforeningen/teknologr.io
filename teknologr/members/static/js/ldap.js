function validatePassword(){
  var password = $('#ldap_password');
  var confirm = $('#confirm_password');
  if(password.val() != confirm.val()) {
    confirm[0].setCustomValidity("Lösenorden är olika");
    confirm.addClass('is-invalid');
  } else if(confirm.val().length <= 0) {
    confirm.removeClass('is-invalid is-valid');
  } else {
    confirm[0].setCustomValidity('');
    confirm.removeClass('is-invalid').addClass('is-valid');
  }
}

$(document).ready(function() {
  $('#confirm_password').keyup(validatePassword);
  $('#ldap_password').change(validatePassword);
});
