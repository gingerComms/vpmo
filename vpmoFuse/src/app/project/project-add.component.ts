import { Component, OnInit } from '@angular/core';
import { NgForm } from '@angular/forms';
import { ProjectService } from './project.service';
import { IProject } from './project';
import { AlertService } from '../_services';
import { MatDatepicker } from '@angular/material';

@Component({
  selector: 'app-project-add',
  templateUrl: './project-add.component.html',
  styleUrls: ['./project-add.component.css']
})
export class ProjectAddComponent implements OnInit {
  project: IProject;

// https://stackblitz.com/angular/krgrvqvrapa?file=styles.css

  constructor(private projectService: ProjectService,
              private alertService: AlertService) { }

   ngOnInit() {
    this.project = {
      id: null,
      projectname: '',
      description: '',
      start: null, // use formatSubmit format to set datepicker value
      owner: 0,
    };
  }


  OnSubmit(form: NgForm) {
    // console.log(this.user);
    // console.log(form.value);
    this.project.owner = JSON.parse(localStorage.getItem('currentUser')).id;
    this.projectService.create(this.project)
      .subscribe(
        data => (console.log('success: ', data)),
                // this.resetForm(form)),
        error => {console.log('error: ', error);
                this.alertService.error(error);
                console.log(form);
        }
                // this.resetForm(form))
      );

  }
}
