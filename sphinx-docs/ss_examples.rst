Screenshot directive example
============================

.. screenshot::
    :user-role: admin
    :navigation-steps: LOGIN prez_obama 123456

.. screenshot::
    :user-role: guest
    :url: /securesync/signup/
    :navigation-steps: #id_username click | NEXT send_keys blah123 | SAME send_keys BACKSPACE BACKSPACE
    :focus: #id_username

.. screenshot::
    :user-role: guest
    :url: /securesync/signup/
    :navigation-steps: #id_username click | NEXT send_keys blah123 | SAME send_keys BACKSPACE BACKSPACE
    :focus: #id_username | Now with annotations!
