from student_testing.utils import set_exam_mode_off


def disable_exam_mode_on_teacher_logout(viewfn):
    """
    Disables exam mode if a teacher is logging out.
    Note that this only applies to teachers, not admins!
    """
    def disable_exam_mode_inner_fcn(request):
        if request.is_teacher:
            set_exam_mode_off()
        return viewfn(request)

    return disable_exam_mode_inner_fcn