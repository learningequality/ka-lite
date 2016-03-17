from fle_utils.config.models import Settings
from securesync.models import Device, Zone, DeviceZone


class CreateDeviceMixin:

    @classmethod
    def setup_fake_device(cls):
        Device.own_device = None
        Settings.set("public_key", u'MIIBCgKCAQEAlbIPLnQH2dORFBK8i9x7/3E0DR571S01aP7M0TJD8vJf8OrgL8pnru3o2Jaoni1XasCZgizvM4GNImk9geqPP/sFkj0cf/MXSLr1VDKo1SoflST9yTbOi7tzVuhTeL4P3LJL6PO6iNiWkjAdqp9QX3mE/DHh/Q40G68meRw6dPDI4z8pyUcshOpxAHTSh2YQ39LJAxP7YS26yjDX/+9UNhetFxemMrBZO0UKtJYggPYRlMZmlTZLBU4ODMmK6MT26fB4DC4ChA3BD4OFiGDHI/iSy+iYJlcWaldbZtc+YfZlGhvsLnJlrp4WYykJSH5qeBuI7nZLWjYWWvMrDepXowIDAQAB')
        Settings.set("private_key", u'-----BEGIN RSA PRIVATE KEY-----\nMIIEqQIBAAKCAQEAlbIPLnQH2dORFBK8i9x7/3E0DR571S01aP7M0TJD8vJf8Org\nL8pnru3o2Jaoni1XasCZgizvM4GNImk9geqPP/sFkj0cf/MXSLr1VDKo1SoflST9\nyTbOi7tzVuhTeL4P3LJL6PO6iNiWkjAdqp9QX3mE/DHh/Q40G68meRw6dPDI4z8p\nyUcshOpxAHTSh2YQ39LJAxP7YS26yjDX/+9UNhetFxemMrBZO0UKtJYggPYRlMZm\nlTZLBU4ODMmK6MT26fB4DC4ChA3BD4OFiGDHI/iSy+iYJlcWaldbZtc+YfZlGhvs\nLnJlrp4WYykJSH5qeBuI7nZLWjYWWvMrDepXowIDAQABAoIBAD8S/a6XGU/BA1ov\n4t4TkvO44TO96nOSTvTkl6x1v4e4dJBwhvHcGP/uIrRQFtA/TpwedxAQmuFa7vrW\n2SHKkX1l6Z0Kvt1yshblH8XQaq8WxqPzKDQGMdVSsHCoB7PScaCOR8nqGGjcyeTi\n/T0NT7JK46vX4N7dgttrE+WixOrtDOUJLX92tGSp8bZgg284fV053nJqYHHROpmZ\nCibM5HK8B/19ULCpglGQCUVmJPtRzNK1bE9OlB8P5aZzdEd82oC8TKfSGmByO1TI\nCat6x8e0hYVIDElYGdcW5CDAr6rbU0CXOxxQAz3gJFDe1/RbbGJEdjO3IulYbR4H\nBK+nGxECgYkA424wFuQGRAwig//SNasv5aIqz2qnczL5ob3MXCFR4aOMowS94qvd\neRG9McxgRwbEApOTMVMAUYlBMkKE//sBM9XWQ4q8igJ+TUlV8RRQ8AP6hMUhSXX0\nNeEECcauP4vI6hhsnTsG/OQ4pr/4bEewsyXFwPSGkh2v3O+fuc6A8RywQ3u6icc+\n9wJ5AKiACZmpSskyJgp+3X0jpYixb7pQ9gU6QpJmP9Z2DdUNnm0Y5tDjnaCd/Bvy\nmNuCWqNbYdlEYH32B3sCshzFCqQwkgSMOa84cHQHx4Nx7SG2fUp9w1ExvnMRzrnw\n3sjB3ptbNhk1yrkzhFbd6ZG4fsL5Mb0EurAFtQKBiFCUVc2GdQHfGsuR9DS3tnyx\n/GEI9NNIGFJKIQHzfENp4wZPQ8fwBMREmLfwJZyEtSYEi35KXi6FZugb0WuwzzhC\nZ2v+19Y+E+nmNeD4xcSEZFpuTeDtPd1pIDkmf85cBI+Mn88FfvBTHA9YrPgQXnba\nxzoaaSOUCR9Kd1kp5V2IQJtoVytBwPkCeFIDD6kkxuuqZu2Q1gkEgptHkZPjt/rP\nYnuTHNsrVowuNr/u8NkXEC+O9Zg8ub2NcsQzxCpVp4lnaDitFTf/h7Bmm4tvHNx1\n4fX3m1oU51ATXGQXVit8xK+JKU9DN4wLIGgJOwmGLwd5VZ5aIEb2v2vykgzn8l2e\nSQKBiQC7CJVToYSUWnDGwCRsF+fY9jUculveAQpVWj03nYBtBdTh2EWcvfoSjjfl\nmpzrraojpQlUhrbUf5MU1fD9+i6swrCCvfjXITG3c1bkkB5AaQW7NiPHvDRMuDpc\nHIQ+vqzdn4iUlt7KB5ChpnZMmgiOdCBM0vQsZlVCbp0ZNLqVYhFASQnWl6V9\n-----END RSA PRIVATE KEY-----\n')
        Device.initialize_own_device()

    @classmethod
    def register_device(cls, zone=None):
        """Register the local device to a zone (dummy zone if none specified)."""
        zone = zone or Zone.objects.create(name='test_zone')
        DeviceZone.objects.create(zone=zone, device=Device.get_own_device())


class CreateZoneMixin:

    @classmethod
    def create_device_zone(cls, zone):
        return DeviceZone.objects.create(device=Device.get_own_device(), zone=zone)

    @classmethod
    def create_zone(cls, **kwargs):
        attr = {
            "name": "zone"
        }
        attr.update(**kwargs)
        return Zone.objects.create(**attr)
