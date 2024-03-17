document.addEventListener('DOMContentLoaded', function () {
  const defaultErrorMessage = 'Server error, please try again later.';
  let hoverTimer = null;

  function handleFetchError(error) {
    console.error('Fetch error:', error);
    let message = defaultErrorMessage;
    if (error.response && error.response.hasOwnProperty('message')) {
      message = error.response.message;
    }
    toast(message, 'error');
  }

  function toast(message, category) {
    const toastEl = document.getElementById('mainToast')
    const toast = bootstrap.Toast.getOrCreateInstance(toastEl)
    toastEl.querySelector('.toast-body').textContent = message

    if (category === 'error') {
      toastEl.classList.replace('text-bg-secondary', 'text-bg-danger')
    } else {
      toastEl.classList.replace('text-bg-danger', 'text-bg-secondary')
    }
    toast.show()
  }

  function showProfilePopover(e) {
    const el = e.target;

    hoverTimer = setTimeout(function () {
      hoverTimer = null;
      fetch(el.dataset.href)
        .then((response) => response.text())
        .then(function (data) {
          const popover = bootstrap.Popover.getOrCreateInstance(el, {
              content: data,
              html: true,
              sanitize: false,
              trigger: 'manual'
            });
          popover.setContent({
            '.popover-body': data
          })
          popover.show();
          document.querySelector('.popover').addEventListener('mouseleave', function () {
            setTimeout(function () {
              popover.hide();
            }, 200);
          });
        })
        .catch(function (error) {
          handleFetchError(error);
        });
    }, 500);
  }

  function hideProfilePopover(e) {
    const el = e.target;

    if (hoverTimer) {
      clearTimeout(hoverTimer);
      hoverTimer = null;
    } else {
      setTimeout(function () {
        if (!document.querySelector('.popover:hover')) {
          const popover = bootstrap.Popover.getInstance(el);
          popover.hide();
        }
      }, 200);
    }
  }

  document.querySelectorAll('.profile-popover').forEach(function (el) {
    el.addEventListener('mouseenter', showProfilePopover);
    el.addEventListener('mouseleave', hideProfilePopover);
  });


  function updateFollowersCount(id) {
    const el = document.getElementById('followers-count-' + id);
    fetch(el.dataset.href)
      .then((response) => response.json())
      .then(function (data) {
        el.textContent = data.count;
      })
      .catch(function (error) {
        handleFetchError(error);
      });
  }

  function updateCollectorsCount(id) {
    const el = document.getElementById('collectors-count-' + id);
    fetch(el.dataset.href)
      .then((response) => response.json())
      .then(function (data) {
        el.textContent = data.count;
      })
      .catch(function (error) {
        handleFetchError(error);
      });
  }

  function updateNotificationsCount() {
    const el = document.getElementById('notification-badge');
    if (!el) {
      return;
    }
    fetch(el.dataset.href)
      .then((response) => response.json())
      .then(function (data) {
        if (data.count === 0) {
          el.style.display = 'none';
        } else {
          el.style.display = 'block';
          el.textContent = data.count;
        }
      })
      .catch(function (error) {
        handleFetchError(error);
      });
  }

  function follow(e) {
    const el = e.target;
    const id = el.dataset.id;
    fetch(el.dataset.href, {
      method: 'POST',
      headers: {
        'X-CSRFToken': csrfToken
      }
    })
      .then((response) => response.json())
      .then(function (data) {
        el.previousElementSibling.style.display = 'inline-block';
        el.style.display = 'none';
        updateFollowersCount(id);
        toast(data.message);
      })
      .catch(function (error) {
        handleFetchError(error);
      });
  }

  function unfollow(e) {
    const el = e.target;
    const id = el.dataset.id;
    fetch(el.dataset.href, {
      method: 'POST',
      headers: {
        'X-CSRFToken': csrfToken
      }
    })
      .then((response) => response.json())
      .then(function (data) {
          el.nextElementSibling.style.display = 'inline-block';
          el.style.display = 'none';
          updateFollowersCount(id);
        toast(data.message);
      })
      .catch(function (error) {
        handleFetchError(error);
      });
  }

  function collect(e) {
    let el = e.target;
    while (el && !el.classList.contains('collect-btn')) {
      el = el.parentElement;
    }
    const id = el.dataset.id;
    fetch(el.dataset.href, {
      method: 'POST',
      headers: {
        'X-CSRFToken': csrfToken
      }
    })
      .then((response) => response.json())
      .then(function (data) {
        el.previousElementSibling.style.display = 'block';
        el.style.display = 'none';
        updateCollectorsCount(id);
        toast(data.message);
      })
      .catch(function (error) {
        handleFetchError(error);
      });
  }

  function uncollect(e) {
    let el = e.target;
    while (el && !el.classList.contains('uncollect-btn')) {
      el = el.parentElement;
    }
    const id = el.dataset.id;
    fetch(el.dataset.href, {
      method: 'POST',
      headers: {
        'X-CSRFToken': csrfToken
      }
    })
      .then((response) => response.json())
      .then(function (data) {
        el.nextElementSibling.style.display = 'block';
        el.style.display = 'none';
        updateCollectorsCount(id);
        toast(data.message);
      })
      .catch(function (error) {
        handleFetchError(error);
      });
  }

  document.addEventListener('click', function (e) {
    if (e.target.classList.contains('follow-btn')) {
      follow(e);
    } else if (e.target.classList.contains('unfollow-btn')) {
      unfollow(e);
    }
  });

  if (document.getElementsByClassName('collect-btn')) {
    document.querySelectorAll('.collect-btn').forEach(function (el) {
      el.addEventListener('click', collect);
    });
  }

  if (document.getElementsByClassName('uncollect-btn')) {
    document.querySelectorAll('.uncollect-btn').forEach(function (el) {
      el.addEventListener('click', uncollect);
    });
  }

  if (document.getElementById('tag-btn')) {
    document.getElementById('tag-btn').addEventListener('click', function () {
      document.getElementById('tags').style.display = 'none';
      document.getElementById('tag-form').style.display = 'block';
    });
  }

  if (document.getElementById('cancel-tag')) {
    document.getElementById('cancel-tag').addEventListener('click', function () {
      document.getElementById('tag-form').style.display = 'none';
      document.getElementById('tags').style.display = 'block';
    });
  }

  if (document.getElementById('description-btn')) {
    document.getElementById('description-btn').addEventListener('click', function () {
      document.getElementById('description').style.display = 'none';
      document.getElementById('description-form').style.display = 'block';
    });
  }

  if (document.getElementById('cancel-description')) {
    document.getElementById('cancel-description').addEventListener('click', function () {
      document.getElementById('description-form').style.display = 'none';
      document.getElementById('description').style.display = 'block';
    });
  }

  if (document.getElementById('confirm-delete')) {
    document.getElementById('confirm-delete').addEventListener('show.bs.modal', function (e) {
      document.querySelector('.delete-form').setAttribute('action', e.relatedTarget.dataset.href);
    });
  }

  if (isAuthenticated) {
    setInterval(updateNotificationsCount, 30000);
  }

  const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'))
  const tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
    return new bootstrap.Tooltip(tooltipTriggerEl)
  });
});
