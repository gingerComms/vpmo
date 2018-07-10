import { Component, OnInit } from '@angular/core';
import { FormBuilder, FormGroup, Validators } from '@angular/forms';

import { FuseConfigService } from '@fuse/services/config.service';
import { fuseAnimations } from '@fuse/animations';
import { Router, ActivatedRoute } from '@angular/router';
import { AuthenticationService } from 'app/_services/authentication.service';
import { AlertService } from 'app/_services/alert.service';

@Component({
    selector   : 'fuse-login',
    templateUrl: './login.component.html',
    styleUrls  : ['./login.component.scss'],
    animations : fuseAnimations
})
export class LoginComponent implements OnInit
{
    loginForm: FormGroup;
    loginFormErrors: any;
    
    model: any = {};
    loading = false;
    returnUrl: string;
    currentUser: any = {};
  

    constructor(
        private fuseConfig: FuseConfigService,
        private formBuilder: FormBuilder,
        private route: ActivatedRoute,
        private router: Router,
        private authenticationService: AuthenticationService,
        private alertService: AlertService,
    )
    {
        this.fuseConfig.setConfig({
            layout: {
                navigation: 'none',
                toolbar   : 'none',
                footer    : 'none'
            }
        });

        this.loginFormErrors = {
            email   : {},
            password: {}
        };
    }

    ngOnInit()
    {
        // reset login status
        this.authenticationService.logout();

        // get return url from route parameters or default to '/'
        this.returnUrl = this.route.snapshot.queryParams['returnUrl'] || '/';
        // this.currentUser = this.authenticationService.currentUser.subscribe(currentUser => this.currentUser);

        this.loginForm = this.formBuilder.group({
            email   : ['', [Validators.required, Validators.email]],
            password: ['', Validators.required]
        });

        this.loginForm.valueChanges.subscribe(() => {
            this.onLoginFormValuesChanged();
        });
    }


    login() {
        this.loading = true;
        this.authenticationService.login(this.loginForm.value.email, this.loginForm.value.password)
            .subscribe(
                data => {
                  console.log(this.model.email);
                  console.log(localStorage.getItem('currentUser'));
                  // this.userLoggedIn.emit(this.model.fullname);
                  this.router.navigate(['/user/dashboard']);
                },
                error => {
                  this.alertService.error(error);
                  this.loading = false;
                });
    }

    
    onLoginFormValuesChanged()
    {
        for ( const field in this.loginFormErrors )
        {
            if ( !this.loginFormErrors.hasOwnProperty(field) )
            {
                continue;
            }

            // Clear previous errors
            this.loginFormErrors[field] = {};

            // Get the control
            const control = this.loginForm.get(field);

            if ( control && control.dirty && !control.valid )
            {
                this.loginFormErrors[field] = control.errors;
            }
        }
    }
}
