from django.conf.urls import patterns, include, url

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    # Examples:
    url(r'^$', 'mweb.views.home', name='home'),

    url(r'^systems/$', 'mweb.views.systems', name='systems'),

    url(r'^system/?P<sys>[a-zA-Z0-9_]+/$', 'mweb.views.system', name='system'),

    url(r'^system/(?P<sys>[a-zA-Z0-9_]+)/(?P<wkr>[a-zA-Z0-9_]+)/$', 'mweb.views.worker', name='worker'),

    url(r'^hosts/$', 'mweb.views.hosts', name='hosts'),

    url(r'^resources/$', 'mweb.views.resources', name='resources'),

    url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    url(r'^admin/', include(admin.site.urls)),
)
