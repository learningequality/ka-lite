import re
import unittest


from django.test import TestCase

import crypto
from securesync.models import Facility, FacilityUser, FacilityGroup
from kalite.utils.django_utils import call_command_with_output


class ChangeLocalUserPassword(unittest.TestCase):
    def setUp(self):
        self.facility = Facility(name="Test Facility")
        self.facility.save()
        self.group = FacilityGroup(facility=self.facility, name="Test Class")
        self.group.full_clean()
        self.group.save()
        self.user = FacilityUser(facility=self.facility, username="testuser", first_name="Firstname", last_name="Lastname", group=self.group)
        self.user.clear_text_password = "testpass" # not used anywhere but by us, for testing purposes
        self.user.set_password(self.user.clear_text_password)
        self.user.full_clean()
        self.user.save()
    
    
    def test_change_password(self):
        
        # Now, re-retrieve the user, to check.
        (out,err,val) = call_command_with_output("changelocalpassword", self.user.username, noinput=True)
        self.assertEquals(err, "", "no output on stderr")
        self.assertNotEquals(out, "", "some output on stderr")
        self.assertEquals(val, 0, "Exit code is zero")
        
        match = re.match(r"^.*Generated new password for user '([^']+)': '([^']+)'", out.replace("\n",""), re.MULTILINE)
        self.assertFalse(match is None, "could not parse stdout")

        user = FacilityUser.objects.get(facility=self.facility, username=self.user.username)
        self.assertEquals(user.username, match.groups()[0], "Username reported correctly")

        self.assertTrue(user.check_password(match.groups()[1]), "New password works")
        self.assertFalse(user.check_password(self.user.clear_text_password), "NOT the old password")
        

    def test_no_user(self):
        fake_username = self.user.username + "xxxxx"
        
        #with self.assertRaises(FacilityUser.DoesNotExist):
        (out,err,val) = call_command_with_output("changelocalpassword", fake_username, noinput=True)

        self.assertNotIn("Generated new password for user", out, "Did not set password")
        self.assertNotEquals(err, "", "some output on stderr")

        match = re.match(r"^.*Error: user '([^']+)' does not exist$", err.replace("\n",""), re.M)
        self.assertFalse(match is None, "could not parse stderr")
        self.assertEquals(match.groups()[0], fake_username, "Verify printed fake username")
        self.assertNotEquals(val, 0, "Verify exit code is non-zero")

@unittest.skipIf(not crypto.M2CRYPTO_EXISTS, "Skipping M2Crypto tests as it does not appear to be installed.")
class TestM2Crypto(unittest.TestCase):

    def setUp(self):
        self.key = crypto.Key()
        self.pykey = crypto.Key(
            private_key_string=self.key.get_private_key_string(),
            public_key_string=self.key.get_public_key_string(),
            use_m2crypto=False)
        self.message_actual = "Hello world! Please leave a message after the tone."
        self.message_fake = "Hello world! Please leave a message after the tone..."
    
    def test_m2crypto_was_used(self):
        # make sure the key was generated using M2Crypto
        self.assertTrue(self.key._using_m2crypto)
        self.assertIsInstance(self.key._private_key, crypto.M2RSA.RSA)

    def test_pyrsa_sig_verification_with_m2crypto(self):
        # make sure something signed with a pyrsa key can be verified by m2crypto
        sig = self.pykey.sign(self.message_actual)
        self.assertTrue(self.key.verify(self.message_actual, sig))
        # make sure it doesn't verify for a different message
        self.assertFalse(self.key.verify(self.message_fake, sig))

    def test_m2crypto_sig_verification_with_pyrsa(self):
        # make sure something signed with an m2crypto key can be verified by pyrsa
        sig = self.key.sign(self.message_actual)
        self.assertTrue(self.pykey.verify(self.message_actual, sig))
        # make sure it doesn't verify for a different message
        self.assertFalse(self.pykey.verify(self.message_fake, sig))

    def test_pubkey_verification_m2crypto(self):
        pubkey = crypto.Key(public_key_string=self.key.get_public_key_string(), use_m2crypto=True)
        sig = self.key.sign(self.message_actual)
        self.assertTrue(pubkey.verify(self.message_actual, sig))
        self.assertFalse(pubkey.verify(self.message_fake, sig))


class TestExistingKeysAndSignatures(unittest.TestCase):

    priv_key_with_pem_header = "-----BEGIN RSA PRIVATE KEY-----\nMIIEogIBAAKCAQEAuABOgZEZ0pxp2hoYnTrYFoqQtzOEeTrjwTULV2v+zjyuT4f/\nIZylz4TH1MgmUMbn7/nu6dsfCYc87hx16fbhcUdZpiAW0Lb0mfnHxUwJKrBHmdr/\nMF8smN1a4OjOJ5O9ugAoijhG+Pb+SUh4tFSRv1vx68CyfxMSK2g/5jGJWlyh1K9Y\noBKXOtsXQQppl+4N4Stve9qFfsyjIW/FNlya3qmQDe9p9r5Ir7YEIS090rCOCEA3\nyiQ8gFThzCVK8Xlu3R/vclrhfvxhJWSJS5z5QRQ0QaZY+/A4b940yDLluRGViHKq\nagMvaKrcTO/fOAa257eSTFUyn7GjxAa9vy8i2QIDAQABAoIBAAiuWwXZ5rH9FzFn\nEco5QICvwOwjzhg6Iwy2h/Zz7e2lB0RRUkQvs9L6nML5PnWJLOAxlogKAojcjI9f\nYGDNeQ1zJFOmJ+1o9FlfY4F3eOc+seIcZvXNR7lemC8MTM2pNsZTw5Xh2dddL9od\nRTSc2NOCbwOEb+d26uCJZpphs+1DZQ5UYPgdu3N+wna5+OdZra1waqZqm1DFKbFT\nVx1PEPH4zyX5jhNP7MFW4W/u96gqAHVaPbkiycuEnxClidZapFrAqaQjFWCA6OPz\nCoNsy+n5fGD5eDIwI/AQQULRAQm35IW6zFmHrdB2q5Aeg87cclhdRnLXx7HQzfWZ\nKetBogECgYEA48mcaU69f4o8E7OCqGKP905MOXT9b1oRC7HRIhcSV3QKlxl/0VY/\nL9A64hn92ByWsyfWbkWjchK3mz2KGi9j1TaoErMLcfxWhcmvHCHIkYjmpilspKfp\nHNAM530C24+7POMcQiT6Q+KIapWyLffpmXHQPd4Z9p11KFx6gQ6hHtECgYEAzspg\nKD0889I32wa0fohHe6fk1Wtv/Fz+SRJ5LYAk/CCfisYDTA2ejayChSXzfPc0oPlb\n9EqBNd6tShhTc1VrJp3F/M4nPN/ZvHzVA/ndu5vpeAiBzdtzjttp3W7Ea01bym++\nOYvnhoDLrG80GCH0nJDCqtuqoYxLvB3Ek8EmlYkCgYAxgSh4Dn/Kjx1dXr7/n2QQ\naDjSp+VIZPedZgjAcukujm6axhTsRuU2m/egGev8IsJxry/ACWxrJzw2BdrUtAXr\nWZSPc9AB9shLDTj8US9Iycruw8PzyPY1p9WWHaoYU5VqtyT2DxlA1aO2HlB6Aw4G\npiCOwY089p12pxqMn8ROcQKBgHJZVnLp6hqp1Fk5i/WsRlsKrG+XyYUzpymhHYEb\nq1gAcji65nfX0CVnj4UxR0ODL4cUXNTpnim7yPeAHCVaxrXD6Qeyt9/hqPWh0ekw\n8nwb6y6FBcJf57bHffMEnXj4fhmjUP1hb9Xgwr/HfncZz7oEEqGIdwJ+IiMUEu/h\njwSBAoGACN/OWrCnLDDqb9kXXIsqx+oJpo311PW39JipU1yEB5Z1PAHw6/qm0PzU\nwCQ+UUbIhdrfdWEs+pPVa4qFNIjVatNdOL5heJzY6ZGQOCV2xv+qX9vuuN962rUk\nmQW3SLGIqqvUDV3Z2nfBwV5L3qbPuGm21PliMUQQOggjx+UIjOo=\n-----END RSA PRIVATE KEY-----"
    priv_key_without_pem_header = "MIIEogIBAAKCAQEAuABOgZEZ0pxp2hoYnTrYFoqQtzOEeTrjwTULV2v+zjyuT4f/\nIZylz4TH1MgmUMbn7/nu6dsfCYc87hx16fbhcUdZpiAW0Lb0mfnHxUwJKrBHmdr/\nMF8smN1a4OjOJ5O9ugAoijhG+Pb+SUh4tFSRv1vx68CyfxMSK2g/5jGJWlyh1K9Y\noBKXOtsXQQppl+4N4Stve9qFfsyjIW/FNlya3qmQDe9p9r5Ir7YEIS090rCOCEA3\nyiQ8gFThzCVK8Xlu3R/vclrhfvxhJWSJS5z5QRQ0QaZY+/A4b940yDLluRGViHKq\nagMvaKrcTO/fOAa257eSTFUyn7GjxAa9vy8i2QIDAQABAoIBAAiuWwXZ5rH9FzFn\nEco5QICvwOwjzhg6Iwy2h/Zz7e2lB0RRUkQvs9L6nML5PnWJLOAxlogKAojcjI9f\nYGDNeQ1zJFOmJ+1o9FlfY4F3eOc+seIcZvXNR7lemC8MTM2pNsZTw5Xh2dddL9od\nRTSc2NOCbwOEb+d26uCJZpphs+1DZQ5UYPgdu3N+wna5+OdZra1waqZqm1DFKbFT\nVx1PEPH4zyX5jhNP7MFW4W/u96gqAHVaPbkiycuEnxClidZapFrAqaQjFWCA6OPz\nCoNsy+n5fGD5eDIwI/AQQULRAQm35IW6zFmHrdB2q5Aeg87cclhdRnLXx7HQzfWZ\nKetBogECgYEA48mcaU69f4o8E7OCqGKP905MOXT9b1oRC7HRIhcSV3QKlxl/0VY/\nL9A64hn92ByWsyfWbkWjchK3mz2KGi9j1TaoErMLcfxWhcmvHCHIkYjmpilspKfp\nHNAM530C24+7POMcQiT6Q+KIapWyLffpmXHQPd4Z9p11KFx6gQ6hHtECgYEAzspg\nKD0889I32wa0fohHe6fk1Wtv/Fz+SRJ5LYAk/CCfisYDTA2ejayChSXzfPc0oPlb\n9EqBNd6tShhTc1VrJp3F/M4nPN/ZvHzVA/ndu5vpeAiBzdtzjttp3W7Ea01bym++\nOYvnhoDLrG80GCH0nJDCqtuqoYxLvB3Ek8EmlYkCgYAxgSh4Dn/Kjx1dXr7/n2QQ\naDjSp+VIZPedZgjAcukujm6axhTsRuU2m/egGev8IsJxry/ACWxrJzw2BdrUtAXr\nWZSPc9AB9shLDTj8US9Iycruw8PzyPY1p9WWHaoYU5VqtyT2DxlA1aO2HlB6Aw4G\npiCOwY089p12pxqMn8ROcQKBgHJZVnLp6hqp1Fk5i/WsRlsKrG+XyYUzpymhHYEb\nq1gAcji65nfX0CVnj4UxR0ODL4cUXNTpnim7yPeAHCVaxrXD6Qeyt9/hqPWh0ekw\n8nwb6y6FBcJf57bHffMEnXj4fhmjUP1hb9Xgwr/HfncZz7oEEqGIdwJ+IiMUEu/h\njwSBAoGACN/OWrCnLDDqb9kXXIsqx+oJpo311PW39JipU1yEB5Z1PAHw6/qm0PzU\nwCQ+UUbIhdrfdWEs+pPVa4qFNIjVatNdOL5heJzY6ZGQOCV2xv+qX9vuuN962rUk\nmQW3SLGIqqvUDV3Z2nfBwV5L3qbPuGm21PliMUQQOggjx+UIjOo="
    priv_key_with_pem_header_unicode = u"-----BEGIN RSA PRIVATE KEY-----\nMIIEogIBAAKCAQEAuABOgZEZ0pxp2hoYnTrYFoqQtzOEeTrjwTULV2v+zjyuT4f/\nIZylz4TH1MgmUMbn7/nu6dsfCYc87hx16fbhcUdZpiAW0Lb0mfnHxUwJKrBHmdr/\nMF8smN1a4OjOJ5O9ugAoijhG+Pb+SUh4tFSRv1vx68CyfxMSK2g/5jGJWlyh1K9Y\noBKXOtsXQQppl+4N4Stve9qFfsyjIW/FNlya3qmQDe9p9r5Ir7YEIS090rCOCEA3\nyiQ8gFThzCVK8Xlu3R/vclrhfvxhJWSJS5z5QRQ0QaZY+/A4b940yDLluRGViHKq\nagMvaKrcTO/fOAa257eSTFUyn7GjxAa9vy8i2QIDAQABAoIBAAiuWwXZ5rH9FzFn\nEco5QICvwOwjzhg6Iwy2h/Zz7e2lB0RRUkQvs9L6nML5PnWJLOAxlogKAojcjI9f\nYGDNeQ1zJFOmJ+1o9FlfY4F3eOc+seIcZvXNR7lemC8MTM2pNsZTw5Xh2dddL9od\nRTSc2NOCbwOEb+d26uCJZpphs+1DZQ5UYPgdu3N+wna5+OdZra1waqZqm1DFKbFT\nVx1PEPH4zyX5jhNP7MFW4W/u96gqAHVaPbkiycuEnxClidZapFrAqaQjFWCA6OPz\nCoNsy+n5fGD5eDIwI/AQQULRAQm35IW6zFmHrdB2q5Aeg87cclhdRnLXx7HQzfWZ\nKetBogECgYEA48mcaU69f4o8E7OCqGKP905MOXT9b1oRC7HRIhcSV3QKlxl/0VY/\nL9A64hn92ByWsyfWbkWjchK3mz2KGi9j1TaoErMLcfxWhcmvHCHIkYjmpilspKfp\nHNAM530C24+7POMcQiT6Q+KIapWyLffpmXHQPd4Z9p11KFx6gQ6hHtECgYEAzspg\nKD0889I32wa0fohHe6fk1Wtv/Fz+SRJ5LYAk/CCfisYDTA2ejayChSXzfPc0oPlb\n9EqBNd6tShhTc1VrJp3F/M4nPN/ZvHzVA/ndu5vpeAiBzdtzjttp3W7Ea01bym++\nOYvnhoDLrG80GCH0nJDCqtuqoYxLvB3Ek8EmlYkCgYAxgSh4Dn/Kjx1dXr7/n2QQ\naDjSp+VIZPedZgjAcukujm6axhTsRuU2m/egGev8IsJxry/ACWxrJzw2BdrUtAXr\nWZSPc9AB9shLDTj8US9Iycruw8PzyPY1p9WWHaoYU5VqtyT2DxlA1aO2HlB6Aw4G\npiCOwY089p12pxqMn8ROcQKBgHJZVnLp6hqp1Fk5i/WsRlsKrG+XyYUzpymhHYEb\nq1gAcji65nfX0CVnj4UxR0ODL4cUXNTpnim7yPeAHCVaxrXD6Qeyt9/hqPWh0ekw\n8nwb6y6FBcJf57bHffMEnXj4fhmjUP1hb9Xgwr/HfncZz7oEEqGIdwJ+IiMUEu/h\njwSBAoGACN/OWrCnLDDqb9kXXIsqx+oJpo311PW39JipU1yEB5Z1PAHw6/qm0PzU\nwCQ+UUbIhdrfdWEs+pPVa4qFNIjVatNdOL5heJzY6ZGQOCV2xv+qX9vuuN962rUk\nmQW3SLGIqqvUDV3Z2nfBwV5L3qbPuGm21PliMUQQOggjx+UIjOo=\n-----END RSA PRIVATE KEY-----"

    pub_key_with_both_headers = "-----BEGIN PUBLIC KEY-----\nMIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAuABOgZEZ0pxp2hoYnTrY\nFoqQtzOEeTrjwTULV2v+zjyuT4f/IZylz4TH1MgmUMbn7/nu6dsfCYc87hx16fbh\ncUdZpiAW0Lb0mfnHxUwJKrBHmdr/MF8smN1a4OjOJ5O9ugAoijhG+Pb+SUh4tFSR\nv1vx68CyfxMSK2g/5jGJWlyh1K9YoBKXOtsXQQppl+4N4Stve9qFfsyjIW/FNlya\n3qmQDe9p9r5Ir7YEIS090rCOCEA3yiQ8gFThzCVK8Xlu3R/vclrhfvxhJWSJS5z5\nQRQ0QaZY+/A4b940yDLluRGViHKqagMvaKrcTO/fOAa257eSTFUyn7GjxAa9vy8i\n2QIDAQAB\n-----END PUBLIC KEY-----\n"
    pub_key_with_pkcs8_header = "MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAuABOgZEZ0pxp2hoYnTrY\nFoqQtzOEeTrjwTULV2v+zjyuT4f/IZylz4TH1MgmUMbn7/nu6dsfCYc87hx16fbh\ncUdZpiAW0Lb0mfnHxUwJKrBHmdr/MF8smN1a4OjOJ5O9ugAoijhG+Pb+SUh4tFSR\nv1vx68CyfxMSK2g/5jGJWlyh1K9YoBKXOtsXQQppl+4N4Stve9qFfsyjIW/FNlya\n3qmQDe9p9r5Ir7YEIS090rCOCEA3yiQ8gFThzCVK8Xlu3R/vclrhfvxhJWSJS5z5\nQRQ0QaZY+/A4b940yDLluRGViHKqagMvaKrcTO/fOAa257eSTFUyn7GjxAa9vy8i\n2QIDAQAB"
    pub_key_with_pem_header = "-----BEGIN RSA PUBLIC KEY-----\nMIIBCgKCAQEAuABOgZEZ0pxp2hoYnTrY\nFoqQtzOEeTrjwTULV2v+zjyuT4f/IZylz4TH1MgmUMbn7/nu6dsfCYc87hx16fbh\ncUdZpiAW0Lb0mfnHxUwJKrBHmdr/MF8smN1a4OjOJ5O9ugAoijhG+Pb+SUh4tFSR\nv1vx68CyfxMSK2g/5jGJWlyh1K9YoBKXOtsXQQppl+4N4Stve9qFfsyjIW/FNlya\n3qmQDe9p9r5Ir7YEIS090rCOCEA3yiQ8gFThzCVK8Xlu3R/vclrhfvxhJWSJS5z5\nQRQ0QaZY+/A4b940yDLluRGViHKqagMvaKrcTO/fOAa257eSTFUyn7GjxAa9vy8i\n2QIDAQAB\n-----END RSA PUBLIC KEY-----\n"
    pub_key_with_no_headers = "MIIBCgKCAQEAuABOgZEZ0pxp2hoYnTrY\nFoqQtzOEeTrjwTULV2v+zjyuT4f/IZylz4TH1MgmUMbn7/nu6dsfCYc87hx16fbh\ncUdZpiAW0Lb0mfnHxUwJKrBHmdr/MF8smN1a4OjOJ5O9ugAoijhG+Pb+SUh4tFSR\nv1vx68CyfxMSK2g/5jGJWlyh1K9YoBKXOtsXQQppl+4N4Stve9qFfsyjIW/FNlya\n3qmQDe9p9r5Ir7YEIS090rCOCEA3yiQ8gFThzCVK8Xlu3R/vclrhfvxhJWSJS5z5\nQRQ0QaZY+/A4b940yDLluRGViHKqagMvaKrcTO/fOAa257eSTFUyn7GjxAa9vy8i\n2QIDAQAB"
    pub_key_with_both_headers_unicode = u"-----BEGIN PUBLIC KEY-----\nMIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAuABOgZEZ0pxp2hoYnTrY\nFoqQtzOEeTrjwTULV2v+zjyuT4f/IZylz4TH1MgmUMbn7/nu6dsfCYc87hx16fbh\ncUdZpiAW0Lb0mfnHxUwJKrBHmdr/MF8smN1a4OjOJ5O9ugAoijhG+Pb+SUh4tFSR\nv1vx68CyfxMSK2g/5jGJWlyh1K9YoBKXOtsXQQppl+4N4Stve9qFfsyjIW/FNlya\n3qmQDe9p9r5Ir7YEIS090rCOCEA3yiQ8gFThzCVK8Xlu3R/vclrhfvxhJWSJS5z5\nQRQ0QaZY+/A4b940yDLluRGViHKqagMvaKrcTO/fOAa257eSTFUyn7GjxAa9vy8i\n2QIDAQAB\n-----END PUBLIC KEY-----\n"
    
    message_actual = "This is the real message."
    message_fake = "This is not the real message."
    
    signature = """\xadkK\xae\xd1\xe4n.\xe7\x90}z\n\xf6\xb2f\xc4%\xa7\x0e\x9c\xe8\xce\xaf\x03\xab\x87\xea\xd4j\x0c"`R\xa3f4\xd7R&W\x1a\xa7\xc2\xa1Y\xd3S\x02m\x07j^W\xa0\x87^\xbcy\xb6z3<\xf5O\x8a\x90\x17bfu\xf9\xb0\x94\xd1\xe6\x1b\xf3\xdf\xc5\xc0\xa3\xf4\xcf\x89>\xd4;\xd1\xef\x89[\xce;\x14\t\xb2\xee/\xdd\rRI]\xae\xae\xff3j\x8ax\x90o\xde\xc3k\xa4\xfbT\xfd\x1a\xdf9<E\xbf\xf5\xfa\x83\xf0\xf6\xa4\xfc\xcc\xeb\x96?\x02\xdaG{\x0e\x06J\x82\xb4\xf3]\xd7\x94\xce(\xdb\x0e\xb7\x8e\x06\x8b)\x01\xe8|x\xc1f\x00\x82X\x8591\xbbn[\x9d\xce`c\x0c*\x9e/\xe7Pox>x8\xcc\xdcH\xbax\xd7xF\xe8a\x196&?\xab\x08\xeaN\x05\xb9\xe7\xaa\xc7\x05\xde\x9c\xdf\xe7\xeeFX\xce\xcd[\x19R\xaaR[\'\xad\xd8\x8fz\xae\x1d\xdf\xdao\xf5\tGU\x89Bl\x84\xc4\xab\x96\xab~RqYK\xa1"""
    signature_base64 = "rWtLrtHkbi7nkH16CvayZsQlpw6c6M6vA6uH6tRqDCJgUqNmNNdSJlcap8KhWdNTAm0Hal5XoIdevHm2ejM89U+KkBdiZnX5sJTR5hvz38XAo/TPiT7UO9HviVvOOxQJsu4v3Q1SSV2urv8zaop4kG/ew2uk+1T9Gt85PEW/9fqD8Pak/Mzrlj8C2kd7DgZKgrTzXdeUzijbDreOBospAeh8eMFmAIJYhTkxu25bnc5gYwwqni/nUG94Png4zNxIunjXeEboYRk2Jj+rCOpOBbnnqscF3pzf5+5GWM7NWxlSqlJbJ63Yj3quHd/ab/UJR1WJQmyExKuWq35ScVlLoQ=="

    @unittest.skipIf(not crypto.M2CRYPTO_EXISTS, "Skipping M2Crypto test as it does not appear to be installed.")
    def test_priv_key_with_pem_header_verification_m2crypto(self):
        key = crypto.Key(private_key_string=self.priv_key_with_pem_header, use_m2crypto=True)
        self.assertTrue(key.verify(self.message_actual, self.signature))
        self.assertFalse(key.verify(self.message_fake, self.signature))

    @unittest.skipIf(not crypto.M2CRYPTO_EXISTS, "Skipping M2Crypto test as it does not appear to be installed.")
    def test_priv_key_with_pem_header_unicode_verification_m2crypto(self):
        key = crypto.Key(private_key_string=self.priv_key_with_pem_header_unicode, use_m2crypto=True)
        self.assertTrue(key.verify(self.message_actual, self.signature))
        self.assertFalse(key.verify(self.message_fake, self.signature))

    @unittest.skipIf(not crypto.M2CRYPTO_EXISTS, "Skipping M2Crypto test as it does not appear to be installed.")
    def test_priv_key_without_pem_header_verification_m2crypto(self):
        key = crypto.Key(private_key_string=self.priv_key_without_pem_header, use_m2crypto=True)
        self.assertTrue(key.verify(self.message_actual, self.signature))
        self.assertFalse(key.verify(self.message_fake, self.signature))
    
    @unittest.skipIf(not crypto.M2CRYPTO_EXISTS, "Skipping M2Crypto test as it does not appear to be installed.")
    def test_pub_key_with_both_headers_verification_m2crypto(self):
        key = crypto.Key(public_key_string=self.pub_key_with_both_headers, use_m2crypto=True)
        self.assertTrue(key.verify(self.message_actual, self.signature))
        self.assertFalse(key.verify(self.message_fake, self.signature))

    @unittest.skipIf(not crypto.M2CRYPTO_EXISTS, "Skipping M2Crypto test as it does not appear to be installed.")
    def test_pub_key_with_both_headers_unicode_verification_m2crypto(self):
        key = crypto.Key(public_key_string=self.pub_key_with_both_headers_unicode, use_m2crypto=True)
        self.assertTrue(key.verify(self.message_actual, self.signature))
        self.assertFalse(key.verify(self.message_fake, self.signature))

    @unittest.skipIf(not crypto.M2CRYPTO_EXISTS, "Skipping M2Crypto test as it does not appear to be installed.")
    def test_pub_key_with_pkcs8_header_verification_m2crypto(self):
        key = crypto.Key(public_key_string=self.pub_key_with_pkcs8_header, use_m2crypto=True)
        self.assertTrue(key.verify(self.message_actual, self.signature))
        self.assertFalse(key.verify(self.message_fake, self.signature))

    @unittest.skipIf(not crypto.M2CRYPTO_EXISTS, "Skipping M2Crypto test as it does not appear to be installed.")
    def test_pub_key_with_pem_header_verification_m2crypto(self):
        key = crypto.Key(public_key_string=self.pub_key_with_pem_header, use_m2crypto=True)
        self.assertTrue(key.verify(self.message_actual, self.signature))
        self.assertFalse(key.verify(self.message_fake, self.signature))

    @unittest.skipIf(not crypto.M2CRYPTO_EXISTS, "Skipping M2Crypto test as it does not appear to be installed.")
    def test_pub_key_with_no_headers_verification_m2crypto(self):
        key = crypto.Key(public_key_string=self.pub_key_with_no_headers, use_m2crypto=True)
        self.assertTrue(key.verify(self.message_actual, self.signature))
        self.assertFalse(key.verify(self.message_fake, self.signature))

    def test_priv_key_with_pem_header_verification_pyrsa(self):
        key = crypto.Key(private_key_string=self.priv_key_with_pem_header, use_m2crypto=False)
        self.assertTrue(key.verify(self.message_actual, self.signature))
        self.assertFalse(key.verify(self.message_fake, self.signature))

    def test_priv_key_with_pem_header_verification_unicode_pyrsa(self):
        key = crypto.Key(private_key_string=self.priv_key_with_pem_header_unicode, use_m2crypto=False)
        self.assertTrue(key.verify(self.message_actual, self.signature))
        self.assertFalse(key.verify(self.message_fake, self.signature))

    def test_priv_key_without_pem_header_verification_pyrsa(self):
        key = crypto.Key(private_key_string=self.priv_key_without_pem_header, use_m2crypto=False)
        self.assertTrue(key.verify(self.message_actual, self.signature))
        self.assertFalse(key.verify(self.message_fake, self.signature))
    
    def test_pub_key_with_both_headers_verification_pyrsa(self):
        key = crypto.Key(public_key_string=self.pub_key_with_both_headers, use_m2crypto=False)
        self.assertTrue(key.verify(self.message_actual, self.signature))
        self.assertFalse(key.verify(self.message_fake, self.signature))

    def test_pub_key_with_both_headers_unicode_verification_pyrsa(self):
        key = crypto.Key(public_key_string=self.pub_key_with_both_headers_unicode, use_m2crypto=False)
        self.assertTrue(key.verify(self.message_actual, self.signature))
        self.assertFalse(key.verify(self.message_fake, self.signature))

    def test_pub_key_with_pkcs8_header_verification_pyrsa(self):
        key = crypto.Key(public_key_string=self.pub_key_with_pkcs8_header, use_m2crypto=False)
        self.assertTrue(key.verify(self.message_actual, self.signature))
        self.assertFalse(key.verify(self.message_fake, self.signature))

    def test_pub_key_with_pem_header_verification_pyrsa(self):
        key = crypto.Key(public_key_string=self.pub_key_with_pem_header, use_m2crypto=False)
        self.assertTrue(key.verify(self.message_actual, self.signature))
        self.assertFalse(key.verify(self.message_fake, self.signature))

    def test_pub_key_with_no_headers_verification_pyrsa(self):
        key = crypto.Key(public_key_string=self.pub_key_with_no_headers, use_m2crypto=False)
        self.assertTrue(key.verify(self.message_actual, self.signature))
        self.assertFalse(key.verify(self.message_fake, self.signature))

    def test_base64_signature_verification(self):
        key = crypto.Key(public_key_string=self.pub_key_with_no_headers)
        self.assertTrue(key.verify(self.message_actual, self.signature_base64))
        self.assertFalse(key.verify(self.message_fake, self.signature_base64))
