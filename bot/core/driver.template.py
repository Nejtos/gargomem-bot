"""
This is a template for a singleton async driver.
The actual configuration, paths, and sensitive data are hidden.
Replace placeholders with your own setup.
"""


class MyDriverTemplate:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(MyDriverTemplate, cls).__new__(cls)
            cls._instance._driver = None
            cls._instance._profNum = None
            cls._instance._closed = False
            cls._instance.browser = None
            cls._instance.page = None
        return cls._instance

    async def init_driver(self, profile_num):
        """
        Initializes the driver.

        Override this method to launch your actual browser/driver and set up browser/page objects.

        Arguments:
            profile_num (int): Profile number or identifier for the driver session.

        Returns:
            driver instance (any): The initialized driver object.

        Notes:
            - self.browser should hold the browser instance.
            - self.page should hold the main page/session object.
        """
        if self._driver is None:
            # Example placeholders. Replace with your real driver initialization.
            self.browser = f"Browser instance for profile {profile_num}"
            self.page = f"Page instance for profile {profile_num}"

            # Simulate navigation or initial setup
            print(f"Initialized driver with profile {profile_num}")
            print("Navigate to your desired start URL here")

            self._driver = self.page
            self._profNum = profile_num
            self._closed = False

        return self._driver

    async def get_driver(self):
        """
        Returns the driver instance if initialized.
        Raises:
            Exception if the driver was not initialized.
        """
        if self._driver is None:
            raise Exception("Driver not initialized. Please call init_driver first.")
        return self._driver

    async def get_profNum(self):
        """
        Returns the profile number associated with the driver.
        Raises:
            Exception if the driver was not initialized.
        """
        if self._profNum is None:
            raise Exception("Profile not detected. Please call init_driver first.")
        return self._profNum

    async def close_driver(self):
        """
        Closes the driver.
        Override this method to properly close your driver and cleanup resources.
        """
        if getattr(self, "browser", None) and not self._closed:
            # Placeholder cleanup. Replace with actual driver/browser cleanup logic.
            print("Closing driver...")

            self._driver = None
            self._profNum = None
            self.page = None
            self.browser = None
            self._instance = None
            self._closed = True
