/* Confirmation dialog for hints. */
$('.hint-unlock').click(function(ev) {
  ev.preventDefault();
  var form = $(ev.target).closest('form');
  var cost = $(form).find('input[name=cost]').val();
  $('#hint-cost').text(cost);
  var modal = $('#hint-modal');
  modal.find('.btn-primary').off('click').click(function() {
    modal.modal('hide');
    form.submit();
  });
  modal.modal('show');
});

/* Add & delete hints */
$('#hint-table').on('click', 'a.delete-hint', function(ev) {
  $(ev.target).closest('tr').remove();
});
$('.add-hint').click(function(ev) {
  var new_hint = "<tr><td><input name='hint-new-hint' class='form-control'></td>" +
      "<td><input name='hint-new-cost' class='form-control'></td>" +
      "<td><a class='delete-hint btn btn-sm btn-warning' " +
      ">&#x2715;</a></td></tr>";
  var tbody = $('#hint-table').find('tbody');
  tbody.append($(new_hint));
});
