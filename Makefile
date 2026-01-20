all: direct_domainset proxy_domainset proxy_routes

direct_domainset:
	@ echo "=====> Building direct domainset"
	@ ./collectors/build_direct_domainset
	@ echo

proxy_domainset:
	@ echo "=====> Building proxy domainset"
	@ ./collectors/build_proxy_domainset
	@ echo

proxy_routes:
	@ echo "=====> Building direct ipset"
	@ ./collectors/build_proxy_routes
	@ echo
