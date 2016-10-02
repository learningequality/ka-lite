from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger


def paginate_data(request, data_list, data_type="cur", per_page=25, page=1):
    """
    Create pagination for list
    """
    if not data_list:
        paged_data = []
        page_urls = {}
    else:
        #Create a Django Pagintor from QuerySet
        paginator = Paginator(data_list, per_page)
        try:
            #Try to render the page with the passed 'page' number
            paged_data = paginator.page(page)
            #Call pages_to_show function that selects a subset of pages to link to
            listed_pages = pages_to_show(paginator, page)
        except PageNotAnInteger:
            #If not a proper page number, render page 1
            paged_data = paginator.page(1)
            #Call pages_to_show function that selects a subset of pages to link to
            listed_pages = pages_to_show(paginator, 1)
        except EmptyPage:
            #If past the end of the page range, render last page
            paged_data = paginator.page(paginator.num_pages)
            #Call pages_to_show function that selects a subset of pages to link to
            listed_pages = pages_to_show(paginator, paginator.num_pages)

    if paged_data:
        #Generate URLs for pagination links
        if paged_data.has_previous():
            #If there are pages before the current page, generate a link for 'previous page'
            prevGETParam = request.GET.copy()
            prevGETParam[data_type + "_page"] = paged_data.previous_page_number()
            previous_page_url = "?" + prevGETParam.urlencode()
        else:
            previous_page_url = ""
        if paged_data.has_next():
            #If there are pages after the current page, generate a link for 'next page'
            nextGETParam = request.GET.copy()
            nextGETParam[data_type + "_page"] = paged_data.next_page_number()
            next_page_url = "?" + nextGETParam.urlencode()
        else:
            next_page_url = ""
        page_urls = {"next_page": next_page_url, "prev_page": previous_page_url}

        if listed_pages:
            #Generate URLs for other linked to pages
            for listed_page in listed_pages:
                if listed_page != -1:
                    GETParam = request.GET.copy()
                    GETParam[data_type + "_page"] = listed_page
                    page_urls.update({listed_page: "?" + GETParam.urlencode()})
            paged_data.listed_pages = listed_pages
            paged_data.num_listed_pages = len(listed_pages)

    return paged_data, page_urls



def pages_to_show(paginator, page, pages_wanted=None, max_pages_wanted=9):
    """
    Function to select first two pages, last two pages and pages around currently selected page
    to show in pagination bar.
    """
    page = int(page)

    #Set precedence for displaying each page on the navigation bar.
    page_precedence_order = [page,1,paginator.num_pages,page+1,page-1,page+2,page-2,2,paginator.num_pages-1]

    if pages_wanted is None:
        pages_wanted = []

    #Allow for arbitrary pages wanted to be set via optional argument
    pages_wanted = set(pages_wanted) or set(page_precedence_order[:max_pages_wanted])

    #Calculate which pages actually exist
    pages_to_show = set(paginator.page_range).intersection(pages_wanted)
    pages_to_show = sorted(pages_to_show)

    #Find gaps larger than 1 in pages_to_show, indicating that a range of pages has been skipped here
    skip_pages = [ x[1] for x in zip(pages_to_show[:-1],
                                     pages_to_show[1:])
                   if (x[1] - x[0] != 1) ]

    #Add -1 to stand in for skipped pages which can then be rendered as an ellipsis.
    for i in skip_pages:
        pages_to_show.insert(pages_to_show.index(i), -1)

    return pages_to_show
